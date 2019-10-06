import socket
import threading
import time
import json

LISTENING_PORT = 41284  # Transaction listening port. DO NOT CHANGE.

# Logic for listening for incoming connections (containing transactions).


class Server:
    def __init__(self, host="localhost", port=LISTENING_PORT):
        self.establishSocket(host, port)

    def establishSocket(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except WindowsError as e:
                if e.winerror == 10048:
                    print(
                        "Port already in use. Please check port usage by other applications, and ensure that the port is open on your network.")
                    exit()
            print("Listening on port " + str(port) + "...")
            s.listen()
            connection, address = s.accept()
            try:
                with connection:
                    while True:
                        data = connection.recv(1024)
                        if data:
                            print("Peer connected - " +
                                  str(address[0]) + ":" + str(address[1]))
                            # Instantiate Broadcast class to broadcast transaction to entire network.
                            broadcast = Broadcast(data)
                            if broadcast.validateTransaction(data):
                                known_nodes = broadcast.getBroadcastNodes()
                                broadcast.sendTransaction(known_nodes)
                            else:
                                print("Invalid transaction. Transaction ignored.")
                        connection.sendall(data)
            except ConnectionAbortedError:
                print("Connection to " +
                      str(address[0]) + ":" + str(address[1]) + " closed.")

# Logic for connecting to known nodes in order to broadcast received transactions.


class Client:
    def __init__(self, host, port, data):
        self.__timeout_counter = 0
        # Create client thread to avoid blocking whilst waiting for reponse from other known nodes.
        thread = threading.Thread(
            target=self.establishSocket, args=(host, port, data))
        thread.start()  # Start thread.

    def establishSocket(self, host, port, data):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                print(host + ":" + str(port) +
                      " - Connected! Sending Transaction...")
            # If connection to node failed, log, and wait 10 seconds to retry.
            except ConnectionRefusedError:
                if self.__timeout_counter >= 10:
                    print(host + ":" + str(port) +
                          " - Connection refused (node may be offline). Connection Timed Out (" + str(self.__timeout_counter) + ")")
                    return
                print(host + ":" + str(port) +
                      " - Connection refused (node may be offline). Retrying in 10 seconds... (" + str(self.__timeout_counter) + ")")
                time.sleep(10)
                self.__timeout_counter += 1
                self.establishSocket(host, port, data)

# Logic for broadcasting transactions to the entire BlockMail network.


class Broadcast:
    def __init__(self, transaction):
        self.__transaction = transaction

    def validateTransaction(self, transaction):
        # try:
        #     transaction_json = json.loads(transaction)
        # except ValueError:
        #     return False
        return True

    def getBroadcastNodes(self):
        with open("known_nodes.txt", "r") as file:
            known_nodes = file.read().split("\n")
        return known_nodes

    def sendTransaction(self, known_nodes):
        print("\n**Broadcasting new Transaction to the Network...**\n\n")
        for node in known_nodes:
            address = node.split(":")
            if node != "":
                host = address[0]
                port = int(address[1])
                client = Client(host, port, self.__transaction)


server = Server()
