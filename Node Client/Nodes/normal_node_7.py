import socket
import threading
import json
import asyncio
import websockets
import time
import random

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain listening port. DO NOT CHANGE.
<<<<<<< Updated upstream
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4", "127.0.0.5", "127.0.0.6", "127.0.0.7", "127.0.0.8"]
SERVER_IP = "127.0.0.15"
=======
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
SERVER_IP = "127.0.0.11"
>>>>>>> Stashed changes

# Logic for listening for incoming connections (containing blockchain information).

<<<<<<< Updated upstream
=======
class NodeServer:
    """Controls communication between nodes on the BlockMail network along with NodeNodeClient.
    Discovers neighbouring nodes.\n
    Takes two arguments:
        host - IP to host server on.
        port - Port to host server on. """
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
            print(f"\nListening on {self.__host}:{self.__port}...")
=======
            print(f"\n[Node Discovery] Listening on {self.__host}:{self.__port}...")
>>>>>>> Stashed changes
            self.acceptConnection(s)  # Accept connections.

    def acceptConnection(self, s):
        connection, address = s.accept()  # Accept data.
        with connection:
            while True:
                data = connection.recv(1024)  # Maximum data stream size of 1024 bytes.
                if data:
                    print(f"\nPeer connected - {str(address[0])}:{str(address[1])}")
                    self.__json_data = self.isJson(data)
<<<<<<< Updated upstream
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

=======
                    if self.__json_data:  # Is data in correct format?  # Is data in correct format?
                        print(f"\n{self.__json_data['origin_host']}:{str(address[1])} - Peer Connected.")
                        if SERVER_IP in MASTER_NODES:
                            self.populateNodesOnNetworkMasters()  # Populate NODES_ON_NETWORK on initial node connection to Master Nodes.
                        else:
                            for node in self.__json_data["nodes_on_network"]:
                                if node not in NODES_ON_NETWORK:
                                    NODES_ON_NETWORK.append(node)
                            while self.discoverNodes():  # Should I be looking for more nodes? (Less than 8 known).
                                self.chooseNodesToAdd()
                    else:
                        print("Not a JSON!")
                break
            print(f"\n{self.__json_data['origin_host']}:{str(address[1])} - Connection Closed.")
            self.acceptConnection(s)

    def discoverNodes(self):
        if len(KNOWN_NODES) < len(MASTER_NODES):  # Should I be discovering more nodes? (Less than 8 known).
            return True
        return False

    def chooseNodesToAdd(self):
        node_index = random.randint(0, len(NODES_ON_NETWORK)-1)  # Randomly choose node to become neighbour.
        if NODES_ON_NETWORK[node_index] not in KNOWN_NODES and NODES_ON_NETWORK[node_index] != SERVER_IP:
            KNOWN_NODES.append(NODES_ON_NETWORK[node_index])  # Add node to known nodes.
            print(f"\nNew Neighbour Found! Neighbouring Nodes: {KNOWN_NODES}")

    def populateNodesOnNetworkMasters(self):
        if self.__json_data["origin_host"] not in NODES_ON_NETWORK:  # Node not already in NODES_ON_NETWORK?
            NODES_ON_NETWORK.append(self.__json_data["origin_host"])  # Add the node to array containing all nodes on network.
            print(f"\nNew Node Joined the Network: {self.__json_data['origin_host']}")
            NodeClient(host=self.__json_data["origin_host"])

>>>>>>> Stashed changes
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


<<<<<<< Updated upstream
class Client:
    previous_connections = []  # Member variable to hold all Client -> Server connections.
=======
class NodeClient:
    """Controls communication between nodes on the BlockMail network along with NodeServer.
    Sends node information to peers.\n
        host - IP of node to connect to.
        port - Port of node to connect to."""
>>>>>>> Stashed changes

    def __init__(self, host, port=DEFAULT_DISCOVERY_PORT, hop=False, server_json=""):
        self.__host = host
        self.__port = port
        self.__hop = hop
        self.__server_json = server_json

        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
<<<<<<< Updated upstream
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
=======
        print(f"\n{self.__host}:{self.__port} - Connecting...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                data_to_send = {"version": VERSION,
                                "origin_host": SERVER_IP,
                                "origin_port": DEFAULT_DISCOVERY_PORT,
                                "nodes_on_network": NODES_ON_NETWORK}
                s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))
            except ConnectionRefusedError:
                print(f"\n{self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry
>>>>>>> Stashed changes


class MailServer:
    """Listens for incoming mail get requests (web page at /mail.html).
    Returns a JSON object of mail objects from Blockchain for requesting address.
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host=SERVER_IP, port=DEFAULT_DISCOVERY_PORT):
        print(f"\n[Mail Server Listening] on ws://{host}:{port}...")
        start_server = websockets.serve(self.establishSocket, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def establishSocket(self, host, port):
        print(host)
        address = await host.recv()
        print(f"\n{address} Requested Mail...")
        await host.send(f"Hello {address}")


if __name__ == "__main__":
<<<<<<< Updated upstream
    for node in MASTER_NODES:
        if node != SERVER_IP:
            client = Client(host=node)  # Port not required as all master nodes use default discovery port.
    server = Server()
=======
    NODES_ON_NETWORK.extend(MASTER_NODES)  # Add all master nodes to NODES_ON_NETWORK to save processing later.
    MailServer()  # Start MailServer.
    if SERVER_IP in MASTER_NODES:
        print(f"*** STARTING MASTER NODE: {SERVER_IP} ***\n")
    else:
        print(f"*** STARTING NODE: {SERVER_IP} ***\n")
    for node in MASTER_NODES:
        if node != SERVER_IP:
            NodeClient(host=node)  # Port not required as all master nodes use default discovery port.
    server = NodeServer()  # Start NodeServer.
>>>>>>> Stashed changes
