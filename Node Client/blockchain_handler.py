import socket
import threading
import json
import time

VERSION = "1.0"
LISTENING_PORT = 41285  # Blockchain listening port. DO NOT CHANGE.

# Logic for listening for incoming connections (containing blockchain information).


class Server:
    def __init__(self, host="localhost", port=LISTENING_PORT):
        print(f"Listing on {host}:{port}...")
        thread = threading.Thread(target=self.establishSocket, args=(host, port))  # Create Server thread to avoid blocking.
        thread.start()  # Start the thread.

    def establishSocket(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((host, port))
            except WindowsError as e:
                if e.winerror == 10048:
                    print("Port already in use. Please check port usage by other applications, and ensure that the port is open on your network.")
                    exit()
            s.listen()
            self.acceptConnection(s, host, port)

    def acceptConnection(self, s, host, port):
        connection, address = s.accept()
        try:
            with connection:
                client = Client(host="localhost", port=41286)
                while True:
                    data = connection.recv(1024)
                    if data:
                        print(f"Peer connected - {str(address[0])}:{str(address[1])}")
                        json_data = self.isJson(data)
                        if json_data:
                            print("JSON!")
                        else:
                            print("Not a JSON!")
                    connection.sendall(data)
        except ConnectionAbortedError:
            print(f"Connection to {str(address[0])}:{str(address[1])} closed.")
            self.acceptConnection(s, host, port)

    def isJson(self, string):
        try:
            json_data = json.loads(string)
        except ValueError:
            return False
        return json_data


class Client:
    def __init__(self, host, port=LISTENING_PORT):
        self.__known_nodes = []
        self.establishSocket(host, port)

    def establishSocket(self, host, port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((host, port))
                data_to_send = {"version": VERSION,
                                "known_nodes": self.__known_nodes}
                s.sendall(bytes(json.dumps(data_to_send), encoding="UTF8"))
            except ConnectionRefusedError:
                    print(f"{host}:{str(port)} - Connection refused (node may be offline). Retrying in 10 seconds...")
                time.sleep(10)
                self.establishSocket(host, port)


server = Server(port=41285)
