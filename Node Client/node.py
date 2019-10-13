import socket
import threading
import time
import random


VERSION = "1.0"


class GeneralFunctions(object):
    @staticmethod
    def readKnownNodes():
        with open("known_nodes.txt", "r") as file:
            known_nodes = file.read().split("\n")
        return known_nodes


class Client:
    def __init__(self, host, port):
        self.establishSocket(host, port)

    def establishSocket(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                known_nodes = GeneralFunctions.readKnownNodes()
                s.connect((host, port))
                s.sendall(bytes("{'version' : " + VERSION + ", "
                                "'known_nodes' : " + str(known_nodes) + "}", "utf-8"))
            except ConnectionRefusedError:
                print(host + ":" + str(port) + " - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)
                self.establishSocket(host, port)


class Server:
    def __init__(self, host, port):
        thread = threading.Thread(target=self.establishSocket, args=(host, port))  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except WindowsError as e:
                if e.winerror == 10048:
                    print("Port already in use. Please check port usage by other applications.")
                    exit()
            print("Listening on port " + str(port) + "...")
            s.listen()
            connection, address = s.accept()
            try:
                with connection:
                    while True:
                        data = connection.recv(1024)
                        if data:
                            # Convert byte string into dictionary.
                            data_dict = eval(data)
                            peer_version = str(data_dict["version"])
                            # Check version of each peer same.
                            if peer_version != VERSION:
                                print("Peer version mismatch (Peer: " + peer_version + ", Self: " + VERSION + ").")
                                s.close()


break
                    print(f"Connection to {str(address[0])}:{str(address[1])} closed.")()
                            else:
                                print("Peer connected - " + str(address[0]) + ":" + str(address[1]))
                                self.updateKnownNodes(data_dict)
                        connection.sendall(data)
            except ConnectionAbortedError:
                print("Connection to " + str(address[0]) + ":" + str(address[1]) + " closed.")

    def updateKnownNodes(self, data_dict):
        # Fetch known nodes from peer.
        peer_known_nodes = data_dict["known_nodes"]
        # Read known nodes for this node into array.
        known_nodes = GeneralFunctions.readKnownNodes()
        # Iterate through all nodes known by peer.
        for i in range(len(peer_known_nodes)):
            # If both this node and the peer share the same known nodes, break.
            if sorted(known_nodes) == sorted(peer_known_nodes):
                break
            # If there are less than 8 known nodes, then choose a node to add randomly from peers known nodes.
            if len(known_nodes) < 8:
                # Keep choosing known nodes from peer, until it doesn't already exist in the array.
                while True:
                    node_to_add = peer_known_nodes[random.randint(0, len(peer_known_nodes) - 1)]
                    if node_to_add not in known_nodes:
                        break
                # Add known node to list.
                known_nodes.append(node_to_add)
        # Write new nodes to file.
        with open("known_nodes.txt", "w") as file:
            for i in range(len(known_nodes)):
                if i != 0:
                    file.write("\n")
                file.write(known_nodes[i])


# server = Server("127.0.0.1", 50430)
# server = Server("127.0.0.1", 50431)
# server = Server("127.0.0.1", 50432)
# server = Server("127.0.0.1", 50433)
# server = Server("127.0.0.1", 50434)
# server = Server("127.0.0.1", 50435)
# known_nodes = GeneralFunctions.readKnownNodes()
# for node in known_nodes:
#     address = node.split(":")
#     host = address[0]
#     port = int(address[1])
client = Client("127.0.0.1", 41285)
