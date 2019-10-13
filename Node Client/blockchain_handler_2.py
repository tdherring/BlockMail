import socket
import threading
import json
import time

VERSION = "1.0"
LISTENING_PORT = 41285  # Blockchain listening port. DO NOT CHANGE.
MASTER_NODES = ["127.0.0.1", "127.0.0.2", "127.0.0.3", "127.0.0.4", "127.0.0.5", "127.0.0.6", "127.0.0.7", "127.0.0.8"]
SERVER_IP = "127.0.0.2"

# Logic for listening for incoming connections (containing blockchain information).


class Server:
    def __init__(self, host=SERVER_IP, port=LISTENING_PORT):
        self.__host = host
        self.__port = port
        self.__known_nodes = []
        self.__number_known_by = 0
        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((self.__host, self.__port))
            except WindowsError as e:
                if e.winerror == 10048:
                    print("Port already in use. Please check port usage by other applications, and ensure that the port is open on your network.")
                    exit()
            s.listen()
            print(f"\nListening on {self.__host}:{self.__port}... (Discovery {self.__number_known_by + 1})")
            self.acceptConnection(s)

    def acceptConnection(self, s):
        connection, address = s.accept()
        with connection:
            while True:
                data = connection.recv(1024)
                if data:
                    print(f"Peer connected - {str(address[0])}:{str(address[1])}")
                    self.__json_data = self.isJson(data)
                    if self.__json_data:  # Is data in correct format
                        if self.discoverNodes():  # Should I be looking for more nodes? (Less than 8 known)
                            self.addKnownNode(f"{self.__json_data['host']}")
                    else:
                        print("Not a JSON!")
                s.close()
                break
            print(f"Connection to {str(address[0])}:{str(address[1])} closed.")
            if self.__number_known_by < 8:  # Should I be open to be discovered? (Less than 8 know me)
                self.establishSocket()

    def isJson(self, string):
        try:
            json_data = json.loads(string)
        except ValueError:
            return False
        return json_data

    def discoverNodes(self):
        if len(self.__known_nodes) < 8:
            return True
        return False

    def addKnownNode(self, node):
        if node not in self.__known_nodes:
            self.__known_nodes.append(node)
            print(f"Node Discovered! Known Nodes: {self.__known_nodes} ({self.__number_known_by})")
            self.__number_known_by += 1  # Increment nodes known by


class Client:
    def __init__(self, host, port=LISTENING_PORT):
        self.__host = host
        self.__port = port
        self.__known_nodes = []
        self.__number_known_by = 0
        thread = threading.Thread(target=self.establishSocket)  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread

    def establishSocket(self):
        print(f"Connecting to {self.__host}:{self.__port}...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.__host, self.__port))
                data_to_send = {"version": VERSION,
                                "host": SERVER_IP,
                                "port": LISTENING_PORT}
                s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))
            except ConnectionRefusedError:
                print(f"{self.__host}:{str(self.__port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)
                self.establishSocket()

    def addToKnown(self):
        self.__known_nodes.append(f"{self.__host}:{self.__port}")


if __name__ == "__main__":
    for node in MASTER_NODES:
        if node != SERVER_IP:
            client = Client(host=node)  # Port not required as all master nodes use default discovery port
    server = Server()
