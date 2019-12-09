import socket
import threading
import json
import websockets
import asyncio
import datetime
import time
import random
import os
import math

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain node discovery port. DO NOT CHANGE.
DEFAULT_MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
SERVER_IP = "127.0.0.2"


class NodeServer:
    """Controls communication between nodes on the BlockMail network along with NodeNodeClient.
    Discovers neighbouring nodes.
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
        received_blockchain_data = ""
        with connection:
            while True:
                data = connection.recv(4096)  # Maximum data stream size of 4096 bytes.
                if data:
                    self.__json_data = self.isJson(data.decode("utf-8"))
                    if self.__json_data:  # Is data in correct format?  # Is data in correct format?
                        if "origin_host" in self.__json_data:
                            origin_host = self.__json_data["origin_host"]
                            print(f"\n[Node Discovery] {self.__json_data['origin_host']}:{str(address[1])} - Peer Connected.")
                            if SERVER_IP in MASTER_NODES:
                                self.populateNodesOnNetworkMasters()  # Populate NODES_ON_NETWORK on initial node connection to Master Nodes.
                            else:
                                for node in self.__json_data["nodes_on_network"]:
                                    if node not in NODES_ON_NETWORK:
                                        NODES_ON_NETWORK.append(node)
                                while self.discoverNodes():  # Should I be looking for more nodes? (Less than number of master nodes known).
                                    self.chooseNodesToAdd()
                        elif "b0" in self.__json_data:
                            print("\n[Blockchain] Blockchain Successfully Updated!")
                            received_blockchain_data = self.__json_data
                            download_blockchain_file = open("downloaded_blockchain.chain", "a+")
                            json.dump(received_blockchain_data, download_blockchain_file)
                            print(received_blockchain_data)
                        else:
                            print("\nData received was JSON, but contents are invalid.")
                    else:
                        decoded_data = data.decode("utf-8")
                        print("\n[Blockchain] Updating Blockchain...")
                        download_blockchain_file = open("downloaded_blockchain.chain", "a+")
                        download_blockchain_file.write(decoded_data)
                        received_blockchain_data += decoded_data
                        if self.isJson(received_blockchain_data):
                            print("\n[Blockchain] Blockchain Successfully Updated!")
                            print(received_blockchain_data)
                            break
                        else:
                            print("\nMalformed Blockchain Data Received.")
            print(f"\n{origin_host}:{str(address[1])} - Connection Closed.")
            self.acceptConnection(s)

    def discoverNodes(self):
        if len(KNOWN_NODES) < len(MASTER_NODES):  # Should I be discovering more nodes? (Less than number of master nodes known).
            return True
        return False

    def chooseNodesToAdd(self):
        node_index = random.randint(0, len(NODES_ON_NETWORK)-1)  # Randomly choose node to become neighbour.
        if NODES_ON_NETWORK[node_index] not in KNOWN_NODES and NODES_ON_NETWORK[node_index] != SERVER_IP:
            KNOWN_NODES.append(NODES_ON_NETWORK[node_index])  # Add node to known nodes.
            print(f"\n[Node Discovery] New Neighbour Found! Neighbouring Nodes: {KNOWN_NODES}")

    def populateNodesOnNetworkMasters(self):
        if self.__json_data["origin_host"] not in NODES_ON_NETWORK:  # Node not already in NODES_ON_NETWORK?
            NODES_ON_NETWORK.append(self.__json_data["origin_host"])  # Add the node to array containing all nodes on network.
            print(f"\n[Node Discovery] New Node Joined the Network: {self.__json_data['origin_host']}")
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
    Sends node information to peers.
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host, port=DEFAULT_DISCOVERY_PORT):
        self.__host = host
        self.__port = port

        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
        RECV_SIZE = 16
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                data_to_send = {"version": VERSION,
                                "origin_host": SERVER_IP,
                                "origin_port": DEFAULT_DISCOVERY_PORT,
                                "nodes_on_network": NODES_ON_NETWORK}
                s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))
                # Send blockchain data.
                segments = int(math.ceil(os.stat("blocks/blockchain.chain").st_size / RECV_SIZE))  # Calculate number of segments to split into.
                blockchain_contents = open("blocks/blockchain.chain", "r").read()
                for position in range(segments):
                    data_to_send = blockchain_contents[position*RECV_SIZE: RECV_SIZE*(position+1)]
                    s.sendall(bytes(data_to_send, encoding="UTF8"))
            except ConnectionRefusedError:
                print(f"\n[Node Discovery] {self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry


class MailServer:
    """Listens for incoming mail requests (web page at /mail.html).
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host=SERVER_IP, port=DEFAULT_MAIL_PORT):
        self.__host = host
        self.__port = port
        start_server = websockets.serve(self.establishSocket, self.__host, self.__port)  # Create websocket listener.
        print(f"\n[Mail Server] Listening on ws://{self.__host}:{self.__port}...")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def establishSocket(self, websocket, path):
        data = await websocket.recv()  # Wait to receive data from client.
        try:
            data_json = json.loads(data)
        except:
            print("[Mail Server] Invalid data stream received. Not a JSON.")
        if data_json["action"] == "GET":
            print(f"\n{self.__host}:{self.__port} ({data_json['body']}) requested mail...")
        elif data_json["action"] == "SEND":
            Mail(data_json["send_addr"], data_json["recv_addr"], data_json["subject"], data_json["body"])
        else:
            print("[Mail Server] Invalid data stream received.")
        await websocket.send("Successfully Connected. Welcome to the BlockMail network!")  # When received, send message back to client.


class Block:
    @staticmethod
    def getAllBlocks():
        all_blocks = {}
        if os.path.exists("blocks/blockchain.chain"):
            all_blocks = open(f"blocks/blockchain.chain", "r").read()
        return all_blocks

    @staticmethod
    def writeToAllBlocks(block_id, data):
        all_blocks_dict = {}
        all_blocks = Block.getAllBlocks()
        if len(all_blocks) != 0:
            all_blocks_dict = eval(all_blocks)
        all_blocks_dict[block_id] = data
        all_blocks = open(f"blocks/blockchain.chain", "w")
        json.dump(all_blocks_dict, all_blocks)

    def __init__(self):
        self.makeDirectory()
        self.newBlock()

    def makeDirectory(self):
        if not os.path.exists("blocks"):
            os.mkdir("blocks")

    def newBlock(self):
        all_blocks_dict = {}
        all_blocks = Block.getAllBlocks()
        if len(all_blocks) != 0:
            all_blocks_dict = eval(all_blocks)
        block_id = f"b{len(all_blocks_dict)}"
        self.__file = open(f"blocks/{block_id}.block", "w+")
        data_to_write = {"block": block_id, "node": f"{SERVER_IP}: {DEFAULT_DISCOVERY_PORT}"}
        json.dump(data_to_write, self.__file)
        Block.writeToAllBlocks(block_id, data_to_write)


class Mail:

    def __init__(self, send_addr, recv_addr, subject, body):
        self.__send_addr = send_addr
        self.__recv_addr = recv_addr
        self.__subject = subject
        self.__body = body
        self.__date_time = datetime.datetime.now()
        self.newMail()

    def newMail(self):
        print(f"\nNEW EMAIL CREATED\n\nSender    : {self.__send_addr}\nRecipient : {self.__recv_addr}\nSubject   : {self.__subject}\nBody      : {self.__body}\nDate/Time : {self.__date_time}")


if __name__ == "__main__":
    NODES_ON_NETWORK.extend(MASTER_NODES)  # Add all master nodes to NODES_ON_NETWORK to save processing later.
    if SERVER_IP in MASTER_NODES:
        print(f"*** STARTING MASTER NODE: {SERVER_IP} ***\n")
    else:
        print(f"*** STARTING NODE: {SERVER_IP} ***\n")
    for node in MASTER_NODES:
        if node != SERVER_IP:
            NodeClient(host=node)  # Port not required as all master nodes use default discovery port.
    Block()
    NodeServer()  # Start NodeServer.
    MailServer()  # Start MailServer.
