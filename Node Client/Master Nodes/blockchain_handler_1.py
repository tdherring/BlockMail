import socket
import threading
import json
import asyncio
import websockets
import time
import random

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain node discovery port. DO NOT CHANGE.
DEFAULT_MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
SERVER_IP = "127.0.0.1"


class NodeServer:
    """Controls communication between nodes on the BlockMail network along with NodeNodeClient.
    Discovers neighbouring nodes.\n
    Takes two arguments:
        host - IP to host server on.
        port - Port to host server on. """

    def __init__(self, host=SERVER_IP, port=DEFAULT_DISCOVERY_PORT):
        self.__host = host
        self.__port = port
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
            print(f"\n[Node Discovery] Listening on {self.__host}:{self.__port}...")
            self.acceptConnection(s)  # Accept connections.

    def acceptConnection(self, s):
        connection, address = s.accept()  # Accept data.
        with connection:
            while True:
                data = connection.recv(1024)  # Maximum data stream size of 1024 bytes.
                if data:
                    print(f"\nPeer connected - {str(address[0])}:{str(address[1])}")
                    self.__json_data = self.isJson(data)
                    if self.__json_data:  # Is data in correct format?  # Is data in correct format?
                        print(f"\n{self.__json_data['origin_host']}:{str(address[1])} - Peer Connected.")
                        if SERVER_IP in MASTER_NODES:
                            self.populateNodesOnNetworkMasters()  # Populate NODES_ON_NETWORK on initial node connection to Master Nodes.
                        else:
                            for node in self.__json_data["nodes_on_network"]:
                                if node not in NODES_ON_NETWORK:
                                    NODES_ON_NETWORK.append(node)
                            while self.discoverNodes():  # Should I be looking for more nodes? (Less than number of master nodes known).
                                self.chooseNodesToAdd()
                    else:
                        print("Not a JSON!")
                break
            print(f"\n{self.__json_data['origin_host']}:{str(address[1])} - Connection Closed.")
            self.acceptConnection(s)

    def discoverNodes(self):
        if len(KNOWN_NODES) < len(MASTER_NODES):  # Should I be discovering more nodes? (Less than number of master nodes known).
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

    def isJson(self, string):
        try:
            json_data = json.loads(string)  # Try to parse JSON.
        except ValueError:
            return False  # If ValueError - not JSON.
        return json_data

    def getJson(self):
        return self.__json_data

# Logic for connecting to other nodes on the BlockMail network.


class NodeClient:
    """Controls communication between nodes on the BlockMail network along with NodeServer.
    Sends node information to peers.\n
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host, port=DEFAULT_DISCOVERY_PORT, hop=False, server_json=""):
        self.__host = host
        self.__port = port
        self.__hop = hop
        self.__server_json = server_json

        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
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


class MailServer:
    """Listens for incoming mail get requests (web page at /mail.html).
    Returns a JSON object of mail objects from Blockchain for requesting address.
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host=SERVER_IP, port=DEFAULT_MAIL_PORT):
        start_server = websockets.serve(self.establishSocket, host, port)
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def establishSocket(self, host, port):
        print(f"\n[Mail Server] Listening on ws://{host}:{port}...")
        uri = f"ws://{host}:{port}"
        async with websockets.connect(uri) as websocket:
            address = await websocket.recv()
            print(f"{address} requested mail...")
            await websocket.send("hello")


if __name__ == "__main__":
    NODES_ON_NETWORK.extend(MASTER_NODES)  # Add all master nodes to NODES_ON_NETWORK to save processing later.
    if SERVER_IP in MASTER_NODES:
        print(f"*** STARTING MASTER NODE: {SERVER_IP} ***\n")
    else:
        print(f"*** STARTING NODE: {SERVER_IP} ***\n")
    for node in MASTER_NODES:
        if node != SERVER_IP:
            NodeClient(host=node)  # Port not required as all master nodes use default discovery port.
    NodeServer()  # Start NodeServer.
    MailServer()  # Start MailServer.
