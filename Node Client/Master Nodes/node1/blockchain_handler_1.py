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
DISCOVERY_PORT = 41285  # Blockchain node discovery port. DO NOT CHANGE.
SYNC_PORT = 41287
BLOCK_PORT = 41288
MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
RECV_SIZE = 256  # The size of the receive buffer on other nodes. DO NOT CHANGE.
SERVER_IP = "127.0.0.1"


class Server(threading.Thread):
    """Controls communication between nodes on the BlockMail network along with NodeClient.
    Discovers neighbouring nodes.\n
    Takes two arguments:
        host - IP to host server on.
        port - Port to host server on. """

    def __init__(self, server_type, port, host=SERVER_IP):
        super(Server, self).__init__()
        self.__server_type = server_type
        self.__host = host
        self.__port = port

    def run(self):
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
            print(f"[{self.__server_type}] Listening on {self.__host}:{self.__port}...")
            self.acceptConnection(s)  # Accept connections.

    def acceptConnection(self, s):
        expected_size = -1
        expected_size_counter = 0
        connection, address = s.accept()  # Accept data.
        with connection:
            while True:
                data = connection.recv(RECV_SIZE)  # Maximum data stream size of 256 bytes.
                if data:
                    decoded_data = data.decode("utf-8")
                    if expected_size == -1:  # Expecting new data stream?
                        hex_length = decoded_data.split("{")[0]
                        expected_size = int(hex_length, 16)  # Convert hex to integer.
                        expected_size_counter = expected_size
                        decoded_data = decoded_data[len(hex_length):]  # Cut size off front
                        self.createTempFile()
                    print(f"[{self.__server_type}] Connection Received... Expecting {expected_size_counter} more bytes of data...")
                    print(decoded_data)
                    self.processIncomingData(decoded_data)  # Store incoming data in file.
                    if expected_size_counter > RECV_SIZE:
                        expected_size_counter -= RECV_SIZE
                    else:  # All data in stream received?
                        expected_size = -1  # Data stream complete, so reset expected_size (Ready for more data).
                        self.__tmp_file.close()
                        print(f"[{self.__server_type}] All Data Received!")
                        self.directToCorrectServer()

    def directToCorrectServer(self):
        if self.__server_type == "DISCOVERY":
            DiscoverySever(self.__tmp_file_name)
        elif self.__server_type == "BLOCKCHAIN":
            SyncServer(self.__tmp_file_name)
        elif self.__server_type == "BLOCK":
            BlockServer(self.__tmp_file_name)

    def createTempFile(self):
        file_num = 1
        file_name_set = False
        while not file_name_set:
            if os.path.exists(f"{self.__server_type + str(file_num)}.tmp"):
                file_num += 1
            else:
                file_name_set = True
        self.__tmp_file_name = f"{self.__server_type + str(file_num)}.tmp"
        self.__tmp_file = open(self.__tmp_file_name, "a+")

    def processIncomingData(self, data):
        self.__tmp_file.write(data)


class DiscoverySever():

    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[DISCOVERY] Discovery Server Started!")
        self.nodeCommunicationControl()

    def nodeCommunicationControl(self):
        json_data = json.loads(open(self.__tmp_file_name, "r").read())
        os.remove(self.__tmp_file_name)  # ... And remove the tmp file.
        print(f"[DISCOVERY] {json_data['origin_host']} - Peer Connected.")
        self.initBlockchainSync(json_data['origin_host'])
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
            print(f"[DISCOVERY] New Node Joined the Network: {json_data['origin_host']}")
            DiscoveryClient(host=json_data["origin_host"])

    def discoverNodes(self):
        if len(KNOWN_NODES) < len(MASTER_NODES):  # Should I be discovering more nodes? (Less than number of master nodes known).
            return True
        return False

    def chooseNodesToAdd(self):
        node_index = random.randint(0, len(NODES_ON_NETWORK)-1)  # Randomly choose node to become neighbour.
        if NODES_ON_NETWORK[node_index] not in KNOWN_NODES and NODES_ON_NETWORK[node_index] != SERVER_IP:
            node = NODES_ON_NETWORK[node_index]
            KNOWN_NODES.append(node)  # Add node to known nodes.
            print(f"[DISCOVERY] New Neighbour Found! Neighbouring Nodes: {KNOWN_NODES}")
            discovery_client_thread = threading.Thread(target=DiscoveryClient, args=(node,))
            sync_client_thread = threading.Thread(target=SyncClient, args=(node,))
            block_client_thread = threading.Thread(target=BlockClient, args=(node,))
            discovery_client_thread.start()
            sync_client_thread.start()
            block_client_thread.start()

    def initBlockchainSync(self, host):
        threading.Thread(target=SyncClient, args=(host,))


class SyncServer():
    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[BLOCKCHAIN] Sync Server Started!")
        self.checkBlockchainUpdate()

    def checkBlockchainUpdate(self):
        if not os.path.exists("blocks"):
            os.mkdir("blocks")
            print("[BLOCKCHAIN] Synchronising Latest Blockchain...")
            shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
            print("[BLOCKCHAIN] Blockchain Successfully Synchronised!")
        else:
            if os.stat(self.__tmp_file_name).st_size > os.stat("blocks/blockchain.chain").st_size:
                print("[BLOCKCHAIN] Updating Blockchain...")
                shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
                print("[BLOCKCHAIN] Blockchain Successfully Updated!")
            else:
                print("[BLOCKCHAIN] Received the Same or Outdated Blockchain. No Changes Made.")
        os.remove(self.__tmp_file_name)  # ... And remove the tmp file.


class BlockServer():
    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[BLOCK] Block Server Started!")
        self.checkBlockSize()

    def checkBlockSize(self):
        block_num = self.getBlockNum()
        if os.path.exists(f"blocks/{block_num}.block"):
            if os.stat(self.__tmp_file_name).st_size > os.stat(f"blocks/{block_num}.block").st_size:
                print("[BLOCK] Larger Block Received! Updating...")
                shutil.copy(self.__tmp_file_name, f"blocks/{block_num}.block")
                print("[BLOCK] Block Successfully Updated!")

                # TODO - ADD TO BLOCKCHAIN.CHAIN
            else:
                print("[BLOCK] Comparing Received Block...")
        else:
            print("[BLOCK] Block Successfully Updated!")
        os.remove(self.__tmp_file_name)  # ... And remove the tmp file.

    def getBlockNum(self):
        for prefix, val_type, value in ijson.parse(open(self.__tmp_file_name, "r")):
            if prefix == "block":
                return value


# Logic for connecting to other nodes on the BlockMail network.
# Unfortunately all of these classes duplicate the establishSocket method. This is a limitaiton with socket objects not supporting
# inheritance. A better solution would have been to have a superclass as with Server.

class DiscoveryClient():

    def __init__(self, host):
        self.__host = host
        self.__port = DISCOVERY_PORT
        self.establishSocket()

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.sendNodeInfo(s)
            except ConnectionRefusedError or ConnectionAbortedError:
                print(f"[DISCOVERY] {self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry

    def sendNodeInfo(self, s):
        data_to_send = {"version": VERSION,
                        "origin_host": SERVER_IP,
                        "origin_port": DISCOVERY_PORT,
                        "nodes_on_network": NODES_ON_NETWORK}
        json_data = json.dumps(data_to_send)
        file_size = hex(len(json_data))
        s.sendall(bytes(file_size + json_data, encoding="UTF8"))


class SyncClient():
    def __init__(self, host):
        self.__host = host
        self.__port = SYNC_PORT
        self.establishSocket()

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.sendBlockchain(s)
            except ConnectionRefusedError:
                print(f"[BLOCKCHAIN] {self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry

    def sendBlockchain(self, s):  # TODO - SEGMENT TO STOP HUGE FILE READ IN
        if os.path.exists("blocks/blockchain.chain"):
            print(f"[BLOCKCHAIN] Sending blockchain to {self.__host}...")
            blockchain_file = open("blocks/blockchain.chain", "r")  # Open this node's copy of the blockchain for reading.
            read_file = blockchain_file.read()
            file_size = hex(len(read_file))
            s.sendall(bytes(file_size + read_file, encoding="UTF8"))
            blockchain_file.close()


class BlockClient():

    def __init__(self, host):
        self.__host = host
        self.__port = BLOCK_PORT
        self.__timeout = 5
        self.establishSocket()

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.broadcastBlock(s)
            except ConnectionRefusedError:
                self.__timeout -= 1
                print(f"[BLOCK] {self.__host} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                if self.__timeout == 0:
                    print(f"[BLOCK] Connection to {self.__host} timed out.")
                    exit()
                self.establishSocket()  # Retry

    def broadcastBlock(self, s):
        while True:
            if Time.block_created.isSet():
                if os.path.exists(f"blocks/{Block.current_block_name}.block") and Block.current_block_name != "":
                    data = eval(open(f"blocks/{Block.current_block_name}.block").read())
                    json_data = json.dumps(data)
                    file_size = hex(len(json_data))
                    print(f"[BLOCK] Broadcasting block ({Block.current_block_name})...")
                    s.sendall(bytes(file_size + json_data, encoding="UTF8"))
                time.sleep(1)  # Ensure only one broadcast / block creation
            time.sleep(0.2)


class Time(threading.Thread):
    block_created = threading.Event()

    @staticmethod
    def getLocalTime():
        return datetime.datetime.now()

    @staticmethod
    def blockCycleDue():
        local_time = Time.getLocalTime()
        if not local_time.second % 20 == 0:
            return False
        return True

    def __init__(self):
        super(Time, self).__init__()

    def run(self):
        self.checkTimeSync()
        while True:
            self.blockTimer()

    def checkTimeSync(self):
        c = ntplib.NTPClient()
        response = c.request("ntp2a.mcc.ac.uk", version=3)
        response.offset
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time, datetime.timezone.utc)
        local_time = datetime.datetime.now()
        if (
            ntp_time.year != local_time.year or ntp_time.month != local_time.month or ntp_time.day !=
            local_time.day or ntp_time.hour != local_time.hour or abs(local_time.second-ntp_time.second) >= 5
        ):
            print("[TIME] This machine's time is too inaccurate. Please resynchronise with an NTP server and restart the client.")
            os._exit(0)

    def blockTimer(self):
        Time.block_created.clear()
        local_time = Time.getLocalTime()
        if local_time.second % 20 == 0:
            Block()
            Time.block_created.set()
            time.sleep(1)
        time.sleep(0.2)


class Block():  # gets to the point when syncing on node 3 where blockchain is overwritten.
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
        if not os.path.exists(f"blocks/{block_id}.block"):
            print(f"[BLOCK] New block ({block_id}) started.")
            self.__file = open(f"blocks/{block_id}.block", "w+")
            data_to_write = {"block": block_id, "node": f"{SERVER_IP}: {DISCOVERY_PORT}"}
            json.dump(data_to_write, self.__file)
            self.writeToAllBlocks(block_id, data_to_write)

    def getAllBlocks(self):
        all_blocks = {}
        if os.path.exists("blocks/blockchain.chain"):
            all_blocks = open(f"blocks/blockchain.chain", "r").read()
        return all_blocks

    def writeToAllBlocks(self, block_id, data):
        all_blocks = self.getAllBlocks()
        all_blocks_dict = {}
        if len(all_blocks) != 0:
            all_blocks_dict = eval(all_blocks)
        all_blocks_dict[block_id] = data
        all_blocks = open(f"blocks/blockchain.chain", "w")
        json.dump(all_blocks_dict, all_blocks)


class MailServer:
    """Listens for incoming mail requests (web page at /mail.html).
        host - IP of node to connect to.
        port - Port of node to connect to."""

    def __init__(self, host=SERVER_IP, port=MAIL_PORT):
        self.__host = host
        self.__port = port
        start_server = websockets.serve(self.establishSocket, self.__host, self.__port)  # Create websocket listener.
        print(f"[MAIL] Listening on ws://{self.__host}:{self.__port}...")
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    async def establishSocket(self, websocket, path):
        data = await websocket.recv()  # Wait to receive data from client.
        try:
            data_json = json.loads(data)
        except:
            print("[MAIL] Invalid data stream received. Not a JSON.")
        if data_json["action"] == "GET":
            print(f"{self.__host}:{self.__port} ({data_json['body']}) requested mail...")
        elif data_json["action"] == "SEND":
            Mail(data_json["send_addr"], data_json["recv_addr"], data_json["subject"], data_json["body"])
        else:
            print("[MAIL] Invalid data stream received.")
        await websocket.send("Successfully Connected. Welcome to the BlockMail network!")  # When received, send message back to client.


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
    time_thread = Time()
    time_thread.start()
    for node in MASTER_NODES:
        if node != SERVER_IP:
            discovery_client_thread = threading.Thread(target=DiscoveryClient, args=(node,))
            discovery_client_thread.start()
    discovery_server_thread = Server("DISCOVERY", DISCOVERY_PORT)
    sync_server_thread = Server("BLOCKCHAIN", SYNC_PORT)
    block_server_thread = Server("BLOCK", BLOCK_PORT)
    discovery_server_thread.start()
    sync_server_thread.start()
    block_server_thread.start()
    MailServer()
