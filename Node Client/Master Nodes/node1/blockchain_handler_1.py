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
BROADCAST_PORT = 41288
MAIL_PORT = 41286  # Blockchain mail exchange port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4"]
NODES_ON_NETWORK = []  # Used only for master nodes to keep track of and assign "known nodes".
KNOWN_NODES = []
CONNECTED_KNOWN_NODES = []
RECV_SIZE = 256  # The size of the receive buffer on other nodes. DO NOT CHANGE.
SERVER_IP = "127.0.0.1"

class Server(threading.Thread):
    """Controls communication between nodes on the BlockMail network along with NodeClient.
    Discovers neighbouring nodes.\n
    Arguments:
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
        while True:
            connection, address = s.accept()  # Accept data.
            server_conn_thread = ServerConnection(connection, address, self.__server_type)
            server_conn_thread.start()  # Thread the connection to allow multiple concurrent connections.


class ServerConnection(threading.Thread):
    """ Threaded. Manages data from other nodes and writes it to files. \n
        Arguments: \n
            connection - Socket, the controller for the connections established from other nodes. 
            address - Socket, '' ''
            server_type - String, Tells this class where to direct the data. """

    def __init__(self, connection, address, server_type):
        super(ServerConnection, self).__init__()
        self.__connection = connection
        self.__address = address
        self.__server_type = server_type
        self.__expected_size = -1
        self.__expected_size_counter = 0

    def run(self):
        while True:
            data = self.__connection.recv(RECV_SIZE)  # Maximum data stream size of 256 bytes.
            decoded_data = data.decode("utf-8")
            if data:
                if self.__expected_size == -1:  # Expecting new data stream?
                    hex_length = decoded_data.split("{")[0]
                    print(decoded_data)
                    self.__expected_size = int(hex_length, 16)  # Convert hex to integer.
                    self.__expected_size_counter = self.__expected_size
                    decoded_data = decoded_data[len(hex_length):]  # Cut size off front
                    self.createTempFile()
                print(f"[{self.__server_type}] Connection Received... Expecting {self.__expected_size_counter} more bytes of data...")
                self.processIncomingData(decoded_data)  # Store incoming data in file.
                if self.__expected_size_counter > RECV_SIZE:
                    self.__expected_size_counter -= RECV_SIZE
                else:  # All data in stream received?
                    self.__expected_size = -1  # Data stream complete, so reset expected_size (Ready for more data).
                    self.__tmp_file.close()
                    print(f"[{self.__server_type}] All Data Received!")
                    self.directToCorrectServer()

    def directToCorrectServer(self):
        if self.__server_type == "DISCOVERY":
            DiscoverySever(self.__tmp_file_name)
        elif self.__server_type == "BLOCKCHAIN":
            SyncServer(self.__tmp_file_name)
        elif self.__server_type == "BROADCAST":
            BroadcastServer(self.__tmp_file_name)

    def createTempFile(self):
        file_num = 1
        file_name_set = False
        while not file_name_set:
            if os.path.exists(f"temp/{self.__server_type + str(file_num)}.tmp"):
                file_num += 1
            else:
                file_name_set = True
        self.__tmp_file_name = f"temp/{self.__server_type + str(file_num)}.tmp"
        self.__tmp_file = open(self.__tmp_file_name, "a+")

    def processIncomingData(self, data):
        self.__tmp_file.write(data)


class DiscoverySever():
    """ Waits for incoming connection from DiscoveryClient() on other nodes. \n
        Arguments: \n
            tmp_file_name - String, passed from ServerConnection() class. Contains temp file name holding connected node information. """

    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[DISCOVERY] Discovery Server Started!")
        self.nodeCommunicationControl()

    def nodeCommunicationControl(self):
        json_data = json.loads(open(self.__tmp_file_name, "r").read())
        if json_data["origin_host"] not in CONNECTED_KNOWN_NODES:
            CONNECTED_KNOWN_NODES.append(json_data['origin_host'])
        print(f"[DISCOVERY] {json_data['origin_host']} - Peer Connected.")
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
            discovery_client_thread.start()

class SyncServer():
    """ Waits for incoming connection from SyncClient() on other nodes. \n
        Arguments: \n
            tmp_file_name - String, passed from ServerConnection() class. Contains temp file name holding up to date blockchain. """


    num_synced = 0  # Keep track of number of blockchains received and synced from other nodes.

    @staticmethod
    def readyToCreateBlocks():
        while not SyncServer.num_synced >= len(CONNECTED_KNOWN_NODES):
            return False
        return True

    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[BLOCKCHAIN] Sync Server Started!")
        self.checkBlockchainUpdate()

    def checkBlockchainUpdate(self):
        if os.path.exists("blocks/blockchain.chain"):
            if os.stat(self.__tmp_file_name).st_size > os.stat("blocks/blockchain.chain").st_size:
                print("[BLOCKCHAIN] Updating Blockchain...")
                shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
                Block(True)
                print("[BLOCKCHAIN] Blockchain Successfully Updated!")
            else:
                print("[BLOCKCHAIN] Received the Same or Outdated Blockchain. No Changes Made.")
            SyncServer.num_synced += 1
        else:
            print("[BLOCKCHAIN] Synchronising Blockchain...")
            shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
            Block(True)
            print("[BLOCKCHAIN] Blockchain Successfully Synchronised!")#
            SyncServer.num_synced += 1


class BroadcastServer():
    """ Waits for incoming emails from other nodes.
        Stores email in current block, and propogates the email further throughout the BlockMail network. \n
        Arguments: \n
            tmp_file_name - String, passed from ServerConnection() class. Contains temp file name holding Email info. """

    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[BROADCAST] Block Server Started!")
        self.addToBlock()

    def addToBlock(self):
        block_num = Block.current_block_name
        print("[BROADCAST] New Email Received, Updating...")
        block_read_in = eval(open(f"blocks/{block_num}.block").read())
        temp_mail_file = eval(open(f"{self.__tmp_file_name}", "r").read())
        block_read_in["mail"].append(temp_mail_file)
        block_file = open(f"blocks/{block_num}.block", "w")
        json.dump(block_read_in, block_file)
        block_file.close()
        print("[BROADCAST] Block Successfully Updated!")
        origin = temp_mail_file["origin_node"]
        self.broadcastFurther(temp_mail_file, origin)

    def broadcastFurther(self, mail, origin):
        for node in CONNECTED_KNOWN_NODES:
            if node != origin:
                broadcast_thread = threading.Thread(target=BroadcastClient, args=(node, mail))
                broadcast_thread.start()


# Logic for connecting to other nodes on the BlockMail network.
# Unfortunately all of these classes duplicate the establishSocket method. This is a limitaiton with socket objects not supporting
# inheritance. A better solution would have been to have a superclass as with Server.

class DiscoveryClient():
    """ Connects to a DiscoveryServer on antoher node. Distributes node information to other nodes. 
        Instantiated on new connection from another node. \n
        Arguments:
            host - String, contains the node IP to conect to. """

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
    """ Connects to a SyncServer on another node. Sends the current blockchain to another node.
        Instantiated upon new connection from another node (at closest future block interval). Called from Block(). \n
        Arguments:
            host - String, contains the node IP to conect to."""

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

class BroadcastClient():
    """ Connects to a BroadcastServer on another node. Distributes Mail throughout network.
        Instantiated upon new email receipt from frontend. \n
        Arguments:
            host - String, contains the node IP to conect to.
            mail - String, the mail data to broadcast."""

    def __init__(self, host, mail):
        self.__host = host
        self.__port = BROADCAST_PORT
        self.__mail = mail
        self.establishSocket()

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # Open a new socket, s.
            try:
                s.connect((self.__host, self.__port))  # Attempt to establish connection at given host and port.
                self.broadcastTransaction(s)
            except ConnectionRefusedError:
                print(f"[BROADCAST] {self.__host} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)  # Wait for 10 seconds
                self.establishSocket()  # Retry

    def broadcastTransaction(self, s):
        file_size = hex(len(self.__mail))
        print(f"[BROADCAST] Broadcasting Email...")
        s.sendall(bytes(file_size + json.dumps(self.__mail), encoding="UTF8"))


class Time(threading.Thread):
    """ Checks the local time against NTP server. Will not allow to run if too out of sync.
        Also periodically dispenses a new block. """

    block_created = threading.Event()

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
            input("\nPress any key to exit...")
            os._exit(0)

    def blockTimer(self):
        Time.block_created.clear()
        local_time = datetime.datetime.now()
        if local_time.second % 10 == 0:
            Block(False)
            Time.block_created.set()
            time.sleep(1)
        time.sleep(0.2)

class Block():
    """ Generates blocks at interval. \n
        sync - Boolean, is this the initial block after sync?"""

    current_block_name = ""
    already_synced = []

    def __init__(self, sync):
        self.__sync = sync
        self.newBlock()
        self.writePrevBlockToChain()
        self.initBlockchainSync()

    def newBlock(self):
        new_block_name = self.getNewBlockName()
        Block.current_block_name = new_block_name
        if not os.path.exists(f"blocks/{new_block_name}.block"):
            print(f"[BLOCK] New block ({new_block_name}) started.")
            self.__file = open(f"blocks/{new_block_name}.block", "w+")
            data_to_write = {"block": new_block_name, "mail": []}
            json.dump(data_to_write, self.__file)

    def getNewBlockName(self):
        blockchain_file = json.load(open("blocks/blockchain.chain", "r"))
        if self.__sync:
            block_name = f"b{str(len(blockchain_file))}"
        else:
            block_name = f"b{str(len(blockchain_file) + 1)}"
        if Block.current_block_name == "" and block_name == "b1":
            return "b0"
        return block_name

    def writePrevBlockToChain(self):
        if not Block.current_block_name in ["", "b0"]:
            block_to_write = f"b{str(int(Block.current_block_name[1:])-1)}"
            if os.path.exists(f"blocks/{block_to_write}.block"):
                blockchain_file = open("blocks/blockchain.chain", "r+b")
                prev_block_file = eval(open(f"blocks/{block_to_write}.block").read())
                blockchain_file.seek(-1, 2)
                if block_to_write == "b0":
                    blockchain_file.write(bytes(f'"{block_to_write}" : {json.dumps(prev_block_file)}' + "}", encoding="UTF8"))
                else:
                    blockchain_file.write(bytes(f', "{block_to_write}" : {json.dumps(prev_block_file)}' + "}", encoding="UTF8"))
                blockchain_file.close()
                

    def initBlockchainSync(self):
        for node in CONNECTED_KNOWN_NODES:
            if node not in Block.already_synced:
                sync_client_thread = threading.Thread(target=SyncClient, args=(node,))
                sync_client_thread.start()
                Block.already_synced.append(node)


class MailServer:
    """ Listens for incoming mail requests (web page at /mail.html). \n
        Arguments: \n
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
        print(data)
        try:
            data_json = json.loads(data)
        except:
            print("[MAIL] Invalid data stream received. Not a JSON.")
        if data_json["action"] == "GET":
            print(f"{self.__host}:{self.__port} ({data_json['body']}) requested mail...")
        elif data_json["action"] == "SEND":
            new_mail_thread = Mail(data_json["send_addr"], data_json["recv_addr"], data_json["subject"], data_json["body"])
            new_mail_thread.start()
        else:
            print("[MAIL] Invalid data stream received.")
        await websocket.send("Successfully Connected. Welcome to the BlockMail network!")  # When received, send message back to client.

    def searchBlockchain(self, websocket, address):  # Need to work on
        email_dict = {}
        for prefix, val_type, value in ijson.parse(open("blocks/blockchain.chain", "r")):
            if prefix == "send_addr" and value == address:
                return value


class Mail(threading.Thread):
    """ Threaded. Takes an incoming email from MailServer(), formats it, and directs it to BroadcastClient() for distribution to other nodes on the network.\n
        Arguments: \n
            send_addr - Sender address of Mail.
            recv_addr - Recipient address of Mail.
            subject - Subject of Mail. 
            body - Body of Mail. """

    def __init__(self, send_addr, recv_addr, subject, body):
        super(Mail, self).__init__()
        self.__send_addr = send_addr
        self.__recv_addr = recv_addr
        self.__subject = subject
        self.__body = body
        self.__date_time = datetime.datetime.now()

    def run(self):
        self.newMail()

    def newMail(self):
        print(f"\nNEW EMAIL CREATED\n\nSender    : {self.__send_addr}\nRecipient : {self.__recv_addr}\nSubject   : {self.__subject}\nBody      : {self.__body}\nDate/Time : {self.__date_time}\nOrigin    :{SERVER_IP}")
        mail_json = {
            "send_addr": self.__send_addr,
            "recv_addr": self.__recv_addr,
            "subject": self.__subject,
            "body": self.__body,
            "datetime": str(self.__date_time),
            "origin_node": SERVER_IP
        }
        block_num = Block.current_block_name
        print(f"[BROADCAST] Adding Email to Current Block ({block_num})...")
        block_read_in = eval(open(f"blocks/{block_num}.block").read())
        block_read_in["mail"].append(mail_json)
        block_file = open(f"blocks/{block_num}.block", "w")
        json.dump(block_read_in, block_file)
        block_file.close()
        print("[BROADCAST] Block Successfully Updated!")
        for node in CONNECTED_KNOWN_NODES:
            broadcast_thread = threading.Thread(target=BroadcastClient, args=(node, mail_json))
            broadcast_thread.start()


if __name__ == "__main__":
    """ Entry point from the program. Sets up and instantiates respective classes. """

    NODES_ON_NETWORK.extend(MASTER_NODES)  # Add all master nodes to NODES_ON_NETWORK to save processing later.
    if SERVER_IP in MASTER_NODES:
        print(f"*** STARTING MASTER NODE: {SERVER_IP} ***\n")
    else:
        print(f"*** STARTING NODE: {SERVER_IP} ***\n")
    # Setup directories
    if not os.path.exists("blocks"):
        os.mkdir("blocks")
    if not os.path.exists("temp"):
        os.mkdir("temp")
    if not os.path.exists("blocks/blockchain.chain"):
        new_blockchain = open("blocks/blockchain.chain", "w+")
        new_blockchain.write("{}")
        new_blockchain.close()
    time_thread = Time()
    time_thread.start()
    for node in MASTER_NODES:
        if node != SERVER_IP:
            discovery_client_thread = threading.Thread(target=DiscoveryClient, args=(node,))
            discovery_client_thread.start()
    discovery_server_thread = Server("DISCOVERY", DISCOVERY_PORT)
    sync_server_thread = Server("BLOCKCHAIN", SYNC_PORT)
    block_server_thread = Server("BROADCAST", BROADCAST_PORT)
    discovery_server_thread.start()
    sync_server_thread.start()
    block_server_thread.start()
    MailServer()
