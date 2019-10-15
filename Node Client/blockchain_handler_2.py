import socket
import threading
import json
import time
import random

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain listening port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4", "127.0.0.5", "127.0.0.6", "127.0.0.7", "127.0.0.8"]
SERVER_IP = "127.0.0.2"

# Logic for listening for incoming connections (containing blockchain information).


class Server:
    def __init__(self, host=SERVER_IP, port=DEFAULT_DISCOVERY_PORT):
        self.__host = host
        self.__port = port
        self.__known_nodes = []
        self.__number_known_by = 0
        self.__json_data = ""
        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.bind((self.__host, self.__port))  # Bind socket to host and port passed to class.
            except WindowsError as e:
                if e.winerror == 10048:  # 10048 - Port blocked error.
                    print("Port already in use. Please check port usage by other applications, and ensure that the port is open on your network.")
                    exit()
                else:
                    print(e)
            s.listen()
            print(f"\nListening on {self.__host}:{self.__port}...")
            self.acceptConnection(s)  # Accept connections.

    def acceptConnection(self, s):
        connection, address = s.accept()  # Accept data.
        with connection:
            while True:
                data = connection.recv(1024)  # Maximum data stream size of 1024 bytes.
                if data:
                    print(f"\nPeer connected - {str(address[0])}:{str(address[1])}")
                    self.__json_data = self.isJson(data)
                    if self.__json_data:  # Is data in correct format?
                        if self.discoverNodes():  # Should I be looking for more nodes? (Less than 8 known).
                            self.addKnownNode(f"{self.__json_data['origin_host']}")  # Add node to known nodes.
                        else:  # Or should I hop to another node? (8 or more known).
                            hop = Hop(self.__json_data, self.__known_nodes)
                            break
                    else:
                        print("Not a JSON!")
                break
            print(f"Connection to {str(address[0])}:{str(address[1])} closed.")
            self.acceptConnection(s)

    def isJson(self, string):
        try:
            json_data = json.loads(string)  # Try to parse JSON.
        except ValueError:
            return False  # If ValueError - not JSON.
        return json_data

    def discoverNodes(self):
        if len(self.__known_nodes) < 8:  # Should I be discovering more nodes? (Less than 8 known).
            return True
        return False

    def addKnownNode(self, node):
        if node not in self.__known_nodes:  # Is node not already known?
            self.__known_nodes.append(node)
            print(f"Node Discovered! Known Nodes: {self.__known_nodes} ({self.__number_known_by + 1})")
            self.__number_known_by += 1  # Increment nodes known by 1.

    def getJson(self):
        return self.__json_data

# Logic for connecting to other nodes on the BlockMail network.


class Client:
    previous_connections = []  # Member variable to hold all Client -> Server connections.

    def __init__(self, host, port=DEFAULT_DISCOVERY_PORT, hop=False, server_json=""):
        self.__host = host
        self.__port = port
        self.__hop = hop
        self.__server_json = server_json

        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
        print(f"Connecting to {self.__host}:{self.__port}...")
        if self.__host not in Client.previous_connections:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
                try:
                    s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                    Client.previous_connections.append(self.__host)
                    data_to_send = {"version": VERSION,
                                    "origin_host": SERVER_IP,
                                    "origin_port": DEFAULT_DISCOVERY_PORT,
                                    "hop": self.__hop}
                    if self.__server_json != "":
                        print(f"Client sees {self.__server_json}")
                        if self.__hop:
                            data_to_send = {"version": VERSION,
                                            "origin_host": self.__server_json["origin_host"],
                                            "origin_port": self.__server_json["origin_port"],
                                            "hop": True}
                            client = Client(host=self.__server_json["origin_host"])
                            print(f"Relaying node information to {self.__server_json['origin_host']}...")
                    s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))
                except ConnectionRefusedError:
                    print(f"{self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                    time.sleep(10)  # Wait for 10 seconds
                    self.establishSocket()  # Retry

# Inherit from Client. Instantiated when a node already knows too many others.
# Passes on the request to another server in order to complete node discovery.


class Hop(Client):
    def __init__(self, json, known_nodes):
        print("\nKnown Nodes full, Hopping...")
        hop_node = self.chooseHopNode(known_nodes)
        super().__init__(host=hop_node, hop=True, server_json=json)  # Call initialiser of parent class, passing through the randomly chosen node to hop to.

    def chooseHopNode(self, known_nodes):
        elected_node = known_nodes[random.randint(0, len(known_nodes)-1)]
        return elected_node


if __name__ == "__main__":
    for node in MASTER_NODES:
        if node != SERVER_IP:
            client = Client(host=node)  # Port not required as all master nodes use default discovery port.
    server = Server()
