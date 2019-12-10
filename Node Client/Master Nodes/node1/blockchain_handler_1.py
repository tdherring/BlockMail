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
import shutil

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain node discovery port. DO NOT CHANGE.
DEFAULT_MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
RECV_SIZE = 4096  # The size of the receive buffer on other nodes. DO NOT CHANGE.
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
                data = connection.recv(4096)  # Maximum data stream size of 4096 bytes.
                if data:
                    json_data = self.isJson(data.decode("utf-8"))
                    if json_data:  # Is data in correct format?
                        if "origin_host" in json_data:
                            origin_host = json_data["origin_host"]
                            print(f"\n[Node Discovery] {json_data['origin_host']}:{str(address[1])} - Peer Connected.")
                            if SERVER_IP in MASTER_NODES:
                                self.populateNodesOnNetworkMasters(json_data)  # Populate NODES_ON_NETWORK on initial node connection to Master Nodes.
                            else:
                                self.populateNodesOnNetwork(json_data)
                                while self.discoverNodes():  # Should I be looking for more nodes? (Less than number of master nodes known).
                                    self.chooseNodesToAdd()
                        elif "b0" in json_data and self.processIncomingBlockchain(data):  # Blockchain Transfer. <= 4096 bytes.
                            break
                        else:
                            print("\nData received was JSON, but contents are invalid.")
                    elif self.processIncomingBlockchain(data):  # Blockchain Transfer. > 4096 bytes (split into various segments - recombine and write to file here)
                        break
            print(f"\n{origin_host}:{str(address[1])} - Connection Closed.")
            self.acceptConnection(s)

    def isJson(self, string):
        try:
            json_data = json.loads(string)  # Try to parse JSON.
        except ValueError:
            return False  # If ValueError - not JSON.
        return json_data

    def populateNodesOnNetwork(self, json_data):
        for node in json_data["nodes_on_network"]:
            if node not in NODES_ON_NETWORK:
                NODES_ON_NETWORK.append(node)

    def populateNodesOnNetworkMasters(self, json_data):
        if json_data["origin_host"] not in NODES_ON_NETWORK:  # Node not already in NODES_ON_NETWORK?
            NODES_ON_NETWORK.append(json_data["origin_host"])  # Add the node to array containing all nodes on network.
            print(f"\n[Node Discovery] New Node Joined the Network: {json_data['origin_host']}")
            NodeClient(host=json_data["origin_host"])

    def discoverNodes(self):
        if len(KNOWN_NODES) < len(MASTER_NODES):  # Should I be discovering more nodes? (Less than number of master nodes known).
            return True
        return False

    def chooseNodesToAdd(self):
        node_index = random.randint(0, len(NODES_ON_NETWORK)-1)  # Randomly choose node to become neighbour.
        if NODES_ON_NETWORK[node_index] not in KNOWN_NODES and NODES_ON_NETWORK[node_index] != SERVER_IP:
            KNOWN_NODES.append(NODES_ON_NETWORK[node_index])  # Add node to known nodes.
            print(f"\n[Node Discovery] New Neighbour Found! Neighbouring Nodes: {KNOWN_NODES}")

    def processIncomingBlockchain(self, data):
        decoded_data = data.decode("utf-8")
        download_blockchain_file = open("downloaded_blockchain.chain", "a+")
        download_blockchain_file.write(decoded_data)
        download_blockchain_file.close()
        if decoded_data[-2:] == "}}":  # End of JSON?
            print(os.stat("downloaded_blockchain.chain").st_size, os.stat("blocks/blockchain.chain").st_size)
            if os.stat("downloaded_blockchain.chain").st_size > os.stat("blocks/blockchain.chain").st_size:
                os.remove("blocks/blockchain.chain")
                shutil.copyfile("downloaded_blockchain.chain", "blocks/blockchain.chain")
                os.remove("downloaded_blockchain.chain")
                print("\n[Blockchain] Blockchain Successfully Updated!")
            else:
                print("\n[Blockchain] Received Outdated Blockchain. No Changes Made.")
            return True
        else:
            print("\n[Blockchain] Updating Blockchain...")
        return False

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
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.sendNodeInfo(s)  # Send information about this node.
                self.sendBlockchain(s)  # Send blockchain data.
            except ConnectionRefusedError:
                print(f"\n[Node Discovery] {self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry

    def sendNodeInfo(self, s):
        data_to_send = {"version": VERSION,
                        "origin_host": SERVER_IP,
                        "origin_port": DEFAULT_DISCOVERY_PORT,
                        "nodes_on_network": NODES_ON_NETWORK}
        s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))

    def sendBlockchain(self, s):
        segments = int(math.ceil(os.stat("blocks/blockchain.chain").st_size / RECV_SIZE))  # Calculate number of segments to split into.
        blockchain_file = open("blocks/blockchain.chain", "r")  # Open this node's copy of the blockchain for reading.
        for position in range(segments):
            data_to_send = blockchain_file.read(RECV_SIZE*(position+1))
            s.sendall(bytes(data_to_send, encoding="UTF8"))
        blockchain_file.close()


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
