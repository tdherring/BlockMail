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
import tempfile
from hashlib import sha256

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
SERVER_IP = "127.0.0.8"


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
            time.sleep(0.5)


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
                    self.__expected_size = int(hex_length, 16)  # Convert hex to integer.
                    self.__expected_size_counter = self.__expected_size
                    decoded_data = decoded_data[len(hex_length):]  # Cut size off front
                    self.createTempFile()
                print(f"[{self.__server_type}] Expecting {self.__expected_size_counter} more bytes of data...")
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
        self.__tmp_file = tempfile.NamedTemporaryFile(mode="a+", delete=False, dir="temp")
        self.__tmp_file_name = self.__tmp_file.name

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
        json_data = json.load(open(self.__tmp_file_name, "r"))
        if json_data["origin_host"] not in CONNECTED_KNOWN_NODES:  # Not already known?
            CONNECTED_KNOWN_NODES.append(json_data['origin_host'])
        print(f"[DISCOVERY] {json_data['origin_host']} - Peer Connected.")
        if json_data['origin_host'] in Block.already_synced:  # Check if node reconnected after disconnect to allow resync.
            Block.already_synced.remove(json_data['origin_host'])
            print(f"[DISCOVERY] Node {json_data['origin_host']} reconnected!")
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


class SyncServer():
    """ Waits for incoming connection from SyncClient() on other nodes. \n
        Arguments: \n
            tmp_file_name - String, passed from ServerConnection() class. Contains temp file name holding up to date blockchain. """

    def __init__(self, tmp_file_name):
        self.__tmp_file_name = tmp_file_name
        print("[BLOCKCHAIN] Sync Server Started!")
        self.checkBlockchainUpdate()

    def checkBlockchainUpdate(self):
        if os.path.exists("blocks/blockchain.chain"):  # Updating an existing blockchain?
            if os.stat(self.__tmp_file_name).st_size > os.stat("blocks/blockchain.chain").st_size:  # Is the blockchain recevied bigger than the current one I hold?
                print("[BLOCKCHAIN] Updating Blockchain...")
                shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")  # Replace the blockchain (copy - overwrite)
                Block(True)  # Create a Block in sync mode.
                print("[BLOCKCHAIN] Blockchain Successfully Updated!")
            else:
                print("[BLOCKCHAIN] Received the Same or Outdated Blockchain. No Changes Made.")
        else:  # Or first chain received.
            print("[BLOCKCHAIN] Synchronising Blockchain...")
            shutil.copy(self.__tmp_file_name, "blocks/blockchain.chain")
            Block(True)  # Create a Block in sync mode.
            print("[BLOCKCHAIN] Blockchain Successfully Synchronised!")


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
        block_read_in = json.load(open(f"blocks/{block_num}.block", "r"))  # Working block.
        temp_mail_file = json.load(open(f"{self.__tmp_file_name}", "r"))  # Received mail.
        block_read_in["mail"].append(temp_mail_file)
        block_file = open(f"blocks/{block_num}.block", "w")
        json.dump(block_read_in, block_file)  # Update block with new mail.
        block_file.close()
        print("[BROADCAST] Block Successfully Updated!")


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
        json_data = json.dumps(data_to_send)  # Convert to string ready for send.
        file_size = hex(len(json_data))  # Get file size in hex.
        s.sendall(bytes(file_size + json_data, encoding="UTF8"))  # Send data.


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
            file_size = hex(len(read_file))  # Get file size in hex.
            s.sendall(bytes(file_size + read_file, encoding="UTF8"))  # Send data.
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
                print(f"[BROADCAST] {self.__host} - Connection refused (node may be offline).")

    def broadcastTransaction(self, s):
        mail_to_send = json.dumps(self.__mail)  # Convert to string ready for send.
        file_size = hex(len(mail_to_send))  # Get file size in hex.
        print(f"[BROADCAST] Broadcasting Email...")
        s.sendall(bytes(file_size + mail_to_send, encoding="UTF8"))  # Send data.


class Time(threading.Thread):
    """ Checks the local time against NTP server. Will not allow to run if too out of sync.
        Also periodically dispenses a new block. """

    block_created = threading.Event()

    def __init__(self):
        super(Time, self).__init__()

    def run(self):
        self.checkTimeSync()
        while True:  # Run infinitely.
            self.blockTimer()

    def checkTimeSync(self):
        c = ntplib.NTPClient()
        response = c.request("ntp2a.mcc.ac.uk", version=3)  # Contact NTP server.
        response.offset
        ntp_time = datetime.datetime.fromtimestamp(response.tx_time, datetime.timezone.utc)  # Convert to datetime object.
        local_time = datetime.datetime.now()  # Get machine time.
        # Compare NTP with local time. If >5s out, reject.
        if (
            ntp_time.year != local_time.year or ntp_time.month != local_time.month or ntp_time.day !=
            local_time.day or ntp_time.hour != local_time.hour or abs(local_time.second-ntp_time.second) >= 5
        ):
            print("[TIME] This machine's time is too inaccurate. Please resynchronise with an NTP server and restart the client.")
            input("\nPress any key to exit...")
            os._exit(0)

    def blockTimer(self):
        Time.block_created.clear()  # Clear the signal.
        local_time = datetime.datetime.now()
        if local_time.second % 30 == 0:
            Block(False)  # Create block at interval in non-sync mode.
            Time.block_created.set()  # Set the signal.
            time.sleep(1)  # Wait for a second to prevent multiple triggers.
        time.sleep(0.2)  # Poll every 0.5s


class Block():
    """ Generates blocks at interval. \n
        Arguments:\n
            sync - Boolean, is this the initial block after sync?"""

    current_block_name = ""
    already_synced = []

    def __init__(self, sync):
        self.__sync = sync
        self.newBlock()
        self.writePrevBlockToChain()
        self.initBlockchainSync()

    def newBlock(self):
        try:  # Try to get a name for the new block.
            new_block_name = self.getNewBlockName()
        except json.decoder.JSONDecodeError:  # If that fails, blockchain hasn't finished updating yet, so recursively retry until successful.
            new_block_name = self.getNewBlockName()
        Block.current_block_name = new_block_name  # Set the class variable for reference for future blocks.
        if not os.path.exists(f"blocks/{new_block_name}.block"):  # Check that the block doesn't already exist.
            print(f"[BLOCK] New block ({new_block_name}) started.")
            self.__file = open(f"blocks/{new_block_name}.block", "w+")
            data_to_write = {"block": new_block_name, "mail": []}
            json.dump(data_to_write, self.__file)  # Write the base block info to the block.

    def getNewBlockName(self):
        blockchain_file = json.load(open("blocks/blockchain.chain", "r"))  # Load json string of blockchain into variable.
        # Generate block name.
        if self.__sync:
            block_name = f"b{str(len(blockchain_file))}"
        else:
            block_name = f"b{str(len(blockchain_file) + 1)}"
        if Block.current_block_name == "" and block_name == "b1":
            return "b0"
        return block_name

    def writePrevBlockToChain(self):
        block_to_write = f"b{str(int(Block.current_block_name[1:])-1)}"  # Set the name of the block to write to.
        if os.path.exists(f"blocks/{block_to_write}.block"):
            blockchain_file = open("blocks/blockchain.chain", "r+b")  # Open file in r+b(ytes) mode. Required to seek.
            prev_block_file = self.generateBlockWithHashDigest(json.load(open(f"blocks/{block_to_write}.block", "r")))
            blockchain_file.seek(-1, 2)  # Go to the 2nd from last position from the end of the file.
            # Define some simple structure to writing to the blockchain JSON in raw format to prevent formatting errors.
            if block_to_write == "b0":
                if not self.__sync:
                    blockchain_file.write(bytes(f'"{block_to_write}" : {json.dumps(prev_block_file)}' + "}", encoding="UTF8"))
            else:
                blockchain_file.write(bytes(f', "{block_to_write}" : {json.dumps(prev_block_file)}' + "}", encoding="UTF8"))
            blockchain_file.close()

    def generateBlockWithHashDigest(self, block):
        hash_digest = sha256(json.dumps(block).encode("utf-8")).hexdigest()
        block["hash_digest"] = hash_digest
        return block

    def initBlockchainSync(self):
        for node in CONNECTED_KNOWN_NODES:
            if node not in Block.already_synced:  # Check that the node has not already received the latest blockchain.
                sync_client_thread = threading.Thread(target=SyncClient, args=(node,))  # Trigger a sync.
                sync_client_thread.start()
                Block.already_synced.append(node)  # Append to record of already synced nodes


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
        try:
            data_json = json.loads(data)
        except:
            print("[MAIL] Invalid data stream received. Not a JSON.")
        if data_json["action"] == "GET":  # Request for mail (on load of /mail.html).
            print(f"{self.__host}:{self.__port} ({data_json['wallet_public']}) requested mail...")
            reply = json.dumps(self.searchBlockchain(data_json["wallet_public"]))
        elif data_json["action"] == "SEND":  # New mail send (generation of keys or actual mail).
            new_mail_thread = Mail(data_json["send_addr"], data_json["recv_addr"], data_json["subject_receiver"], data_json["subject_sender"], data_json["body_receiver"], data_json["body_sender"])
            new_mail_thread.start()
            reply = "Email Sent!"
        elif data_json["action"] == "KEY":  # Search for public key when sending mail.
            reply = json.dumps(self.getPublicKeys(data_json["recv_addr"], data_json["send_addr"]))
        else:
            print("[MAIL] Invalid data stream received.")
        await websocket.send(reply)  # When received, send message back to client.

    def searchBlockchain(self, address):
        all_emails = []
        fetching_email = False  # Allows for "backtracking".
        current_email = {}
        send_addr = ""
        for prefix, val_type, value in ijson.parse(open("blocks/blockchain.chain", "r")):
            if prefix.endswith("send_addr"):
                send_addr = value
            if (prefix.endswith("send_addr") or prefix.endswith("recv_addr")) and value == address:
                fetching_email = True
            if fetching_email:
                current_email["send_addr"] = send_addr
                if prefix.endswith("recv_addr"):
                    current_email["recv_addr"] = value
                elif prefix.endswith("subject_sender") and send_addr == address:  # Requested by sender?
                    current_email["subject"] = value
                elif prefix.endswith("subject_receiver") and send_addr != address:  # Requested by receiver?
                    current_email["subject"] = value
                elif prefix.endswith("body_sender") and send_addr == address:
                    current_email["body"] = value
                elif prefix.endswith("body_receiver") and send_addr != address:
                    current_email["body"] = value
                elif prefix.endswith("datetime"):
                    current_email["datetime"] = value
                elif prefix.endswith("origin_node"):
                    current_email["origin_node"] = value
                    if not current_email["recv_addr"] == "0x0":  # Don't append the initial key mail.
                        all_emails.append(current_email)
                    current_email = {}
                    fetching_email = False
        return {"emails": all_emails[::-1]}

    def getPublicKeys(self, recv_address, send_address):
        fetching_recv_key = False
        fetching_send_key = False
        num_fetched = 0
        keys = {}
        for prefix, val_type, value in ijson.parse(open("blocks/blockchain.chain", "r")):
            # Receiver key.
            if prefix.endswith("send_addr") and (value == recv_address):
                fetching_recv_key = True
            if fetching_recv_key and prefix.endswith("body_sender"):
                fetching_recv_key = False
                num_fetched += 1
                keys["recv_key"] = value
            # Sender key.
            if prefix.endswith("send_addr") and (value == send_address):
                fetching_send_key = True
            if fetching_send_key and prefix.endswith("body_sender"):
                fetching_send_key = False
                num_fetched += 1
                keys["send_key"] = value
            if num_fetched == 2:
                return keys


class Mail(threading.Thread):
    """ Threaded. Takes an incoming email from MailServer(), formats it, and directs it to BroadcastClient() for distribution to other nodes on the network.\n
        Arguments: \n
            send_addr - Sender address of Mail.
            recv_addr - Recipient address of Mail.
            subject - Subject of Mail. 
            body - Body of Mail. """

    def __init__(self, send_addr, recv_addr, subject_receiver, subject_sender, body_receiver, body_sender):
        super(Mail, self).__init__()
        self.__send_addr = send_addr
        self.__recv_addr = recv_addr
        self.__subject_receiver = subject_receiver
        self.__subject_sender = subject_sender
        self.__body_receiver = body_receiver
        self.__body_sender = body_sender
        self.__date_time = datetime.datetime.now()

    def run(self):
        self.newMail()

    def newMail(self):
        print(f"\nNEW EMAIL CREATED\n\nSender    : {self.__send_addr}\nRecipient : {self.__recv_addr}\nSubject (Recv): {self.__subject_receiver}\nSubject (Send): {self.__subject_sender}\n \
                Body (Recv) : {self.__body_receiver}\nBody (Send) : {self.__body_sender}\nDate/Time : {self.__date_time}\nOrigin    : {SERVER_IP}\n")
        mail_json = {
            "send_addr": self.__send_addr,
            "recv_addr": self.__recv_addr,
            "subject_receiver": self.__subject_receiver,
            "subject_sender": self.__subject_sender,
            "body_receiver": self.__body_receiver,
            "body_sender": self.__body_sender,
            "datetime": str(self.__date_time),
            "origin_node": SERVER_IP
        }
        block_num = Block.current_block_name  # Fetch the current block.
        print(f"[BROADCAST] Adding Email to Current Block ({block_num})...")
        block_read_in = json.load(open(f"blocks/{block_num}.block", "r"))
        block_read_in["mail"].append(mail_json)  # Add the email to the current block.
        block_file = open(f"blocks/{block_num}.block", "w")
        json.dump(block_read_in, block_file)  # Update the block with the new mail.
        block_file.close()
        print("[BROADCAST] Block Successfully Updated!")
        # Broadcast the email to all known nodes.
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
