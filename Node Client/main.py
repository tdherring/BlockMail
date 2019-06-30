from ellipticcurve.ecdsa import Ecdsa
import random
import socket

SEED_ADDRESSES = [["localhost", 50432]]
VERSION = 1.0

class ClientConnection:
    def chooseNode(self):
        return SEED_ADDRESSES[random.randint(0, len(SEED_ADDRESSES) - 1)]

    def establishSocket(self):
        FIRST_NODE_IP = self.chooseNode()[0]
        FIRST_NODE_PORT = self.chooseNode()[1]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((FIRST_NODE_IP, FIRST_NODE_PORT))
            s.sendall(b"Hello world")

class Server:
    def __init__(self):
        self.establishSocket()

    def establishSocket(self):
        HOST = "localhost"
        PORT = 50436
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((HOST, PORT))
            s.listen()
            connection, address = s.accept()
            with connection:
                print("Connected by", address)
                while True:
                    data = connection.recv(1024)
                    if not data:
                        break
                    connection.sendall(data)