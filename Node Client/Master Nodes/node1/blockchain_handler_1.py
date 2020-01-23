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
import ijson
import ntplib

VERSION = "1.0"
DEFAULT_DISCOVERY_PORT = 41285  # Blockchain node discovery port. DO NOT CHANGE.
DEFAULT_MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
RECV_SIZE = 256  # The size of the receive buffer on other nodes. DO NOT CHANGE.
SERVER_IP = "127.0.0.1"


class NodeServer(threading.Thread):
    """Controls communication between nodes on the BlockMail network along with NodeNodeClient.
    Discovers neighbouring nodes.\n
    Takes two arguments:
        host - IP to host server on.
        port - Port to host server on. """

    def __init__(self, host=SERVER_IP, port=DEFAULT_DISCOVERY_PORT):
        super(NodeServer, self).__init__()
        self.__host = host
        self.__port = port

    def run(self):  # Required by threading module. DO NOT RENAME.
        self.establishSocket()

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
        expected_size = -1
        connection, address = s.accept()  # Accept data.
        with connection:
            while True:
                data = connection.recv(RECV_SIZE)  # Maximum data stream size of 256 bytes.
                if data:
                    decoded_data = data.decode("utf-8")
                    print(decoded_data)
                    if expected_size == -1:  # Expecting new data stream?
                        hex_length = decoded_data.split("{")[0]
                        expected_size = int(hex_length, 16)  # Convert hex to integer.
                        decoded_data = decoded_data[len(hex_length):]  # Cut size off front
                    print(f"\n[Communication] Connection Received... Expecting {expected_size} bytes of data.")
                    self.processIncomingData(decoded_data)  # Store incoming data in file.
                    print(os.stat(self.__tmp_file_name).st_size, expected_size)
                    if os.stat(self.__tmp_file_name).st_size == expected_size:  # All data in stream received?
                        self.checkDataType()
                        expected_size = -1  # Data stream complete, so reset expected_size (Ready for more data).
                        os.remove(self.__tmp_file_name)  # ... And remove the tmp file.

    def processIncomingData(self, data):
        file_num = 1
        file_name_set = False
        while not file_name_set:
            try:
                self.__tmp_file_name = f"tmp_in_{str(file_num)}.tmp"
                tmp_file = open(self.__tmp_file_name, "a+")
                file_name_set = True
            except:
                file_num += 1
                self.__tmp_file_name = f"tmp_in_{str(file_num)}.tmp"
                tmp_file = open(self.__tmp_file_name, "a+")
        tmp_file.write(data)
        tmp_file.close()

    def checkDataType(self):
        for prefix, val_type, value in ijson.parse(open(self.__tmp_file_name, "r")):  # Iterate through JSON (which may be huge!). Avoid reading into memory.
            if prefix == "type" and value == "NODE_COMMS":
                self.nodeCommunicationControl()
                break
            elif prefix == "type" and value == "BLOCKCHAIN":
                self.checkBlockchainUpdate()
                break
            elif prefix == "type" and value == "BLOCK":
                print("\nBLOCK RECEIVED")
                break

    def checkBlockchainUpdate(self):
        if os.stat(self.__tmp_file_name).st_size > os.stat("blocks/blockchain.chain").st_size:
            print("\n[Blockchain] Updating Blockchain...")
            shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
            print("\n[Blockchain] Blockchain Successfully Updated!")
        else:
            print("\n[Blockchain] Received the Same or Outdated Blockchain. No Changes Made.")

    def nodeCommunicationControl(self):
        json_data = json.loads(open(self.__tmp_file_name, "r").read())
        print(f"\n[Node Discovery] {json_data['origin_host']} - Peer Connected.")
        if SERVER_IP in MASTER_NODES:
            self.populateNodesOnNetworkMasters(json_data)  # Populate NODES_ON_NETWORK on initial node connection to Master Nodes.
        self.populateNodesOnNetwork(json_data)
        while self.discoverNodes():  # Should I be looking for more nodes? (Less than number of master nodes known).
            self.chooseNodesToAdd()

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


# Logic for connecting to other nodes on the BlockMail network.


class NodeClient(threading.Thread):
    """Controls communication between nodes on the BlockMail network along with NodeServer.
    Sends node information to peers.
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host, port=DEFAULT_DISCOVERY_PORT):
        super(NodeClient, self).__init__()
        self.__host = host
        self.__port = port

    def run(self):  # Required by threading module. DO NOT RENAME.
        self.establishSocket()

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.sendNodeInfo(s)  # Send information about this node.
                self.sendBlockchain(s)  # Send blockchain data.
                while True:
                    local_time = Time.getLocalTime()
                    if local_time.second == 0:
                        print(local_time)
                        self.broadcastBlock(s)
                        time.sleep(1)  # Ensure only one broadcast
                    time.sleep(0.2)
            except ConnectionRefusedError:
                print(f"\n[Node Discovery] {self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry

    def sendNodeInfo(self, s):
        data_to_send = {"type": "NODE_COMMS",
                        "version": VERSION,
                        "origin_host": SERVER_IP,
                        "origin_port": DEFAULT_DISCOVERY_PORT,
                        "nodes_on_network": NODES_ON_NETWORK}
        json_data = json.dumps(data_to_send)
        file_size = hex(len(json_data))
        s.sendall(bytes(file_size + json_data, encoding="UTF8"))

    def sendBlockchain(self, s):  # TODO - SEGMENT TO STOP HUGE FILE READ IN
        blockchain_file = open("blocks/blockchain.chain", "r")  # Open this node's copy of the blockchain for reading.
        read_file = blockchain_file.read()
        file_size = hex(len(read_file))
        s.sendall(bytes(file_size + read_file, encoding="UTF8"))
        blockchain_file.close()

    def broadcastBlock(self, s):
        data_to_send = {"type": "BLOCK"}
        data_to_send.update(eval(open(f"blocks/{Block.current_block_name}.block").read()))
        json_data = json.dumps(data_to_send)
        file_size = hex(len(json_data))
        s.sendall(bytes(file_size + json_data, encoding="UTF8"))


class Time(threading.Thread):
    """Ensures that Timing is accurate to keep block timings correct (enough).
    Threaded, runs a check every 5 minutes. If the client becomes out of sync, exit."""

    @staticmethod
    def getLocalTime():
        return datetime.datetime.now()

    def __init__(self):
        super(Time, self).__init__()

    def run(self):
        while True:
            self.checkTimeSync()
            time.sleep(300)

    def checkTimeSync(self):
        c = ntplib.NTPClient()
        response = c.request("ntp2a.mcc.ac.uk", version=3)
        response.offset
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time, datetime.timezone.utc)
        local_time = datetime.datetime.now()
        if (
            ntp_time.year != local_time.year or ntp_time.month != local_time.month or ntp_time.day != local_time.day or ntp_time.hour
            != local_time.hour or ntp_time.second != local_time.second or abs(local_time.microsecond-ntp_time.microsecond) > 50000
        ):
            print("\n[Time Error] This machine's time is too inaccurate. Please resynchronise with an NTP server and restart the client.")
            os._exit(0)


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


class Block():
    current_block_name = ""

    def __init__(self):
        self.makeDirectory()
        self.newBlock()

    def makeDirectory(self):
        if not os.path.exists("blocks"):
            os.mkdir("blocks")

    def newBlock(self):
        all_blocks_dict = {}
        all_blocks = self.getAllBlocks()
        if len(all_blocks) != 0:
            all_blocks_dict = eval(all_blocks)
        block_id = f"b{len(all_blocks_dict)}"
        Block.current_block_name = block_id
        self.__file = open(f"blocks/{block_id}.block", "w+")
        data_to_write = {"block": block_id, "node": f"{SERVER_IP}: {DEFAULT_DISCOVERY_PORT}"}
        json.dump(data_to_write, self.__file)
        self.writeToAllBlocks(block_id, data_to_write)

    def getAllBlocks(self):
        all_blocks = {}
        if os.path.exists("blocks/blockchain.chain"):
            all_blocks = open(f"blocks/blockchain.chain", "r").read()
        return all_blocks

    def writeToAllBlocks(self, block_id, data):
        all_blocks_dict = {"type": "BLOCKCHAIN"}
        all_blocks = self.getAllBlocks()
        if len(all_blocks) != 0:
            all_blocks_dict.update(eval(all_blocks))
        all_blocks_dict[block_id] = data
        all_blocks = open(f"blocks/blockchain.chain", "w")
        json.dump(all_blocks_dict, all_blocks)


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
    Block()
    for node in MASTER_NODES:
        if node != SERVER_IP:
            node_client_thread = NodeClient(host=node)  # Port not required as all master nodes use default discovery port.
            node_client_thread.start()
    node_server_thread = NodeServer()
    time_thread = Time()
    time_thread.start()
    node_server_thread.start()
    MailServer()
