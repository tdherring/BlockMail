from ecdsa import SigningKey, VerifyingKey, SECP256k1
from hashlib import sha256
import rsa
import json
import asyncio
import websockets


class Mail:
    def __init__(self, from_addr, to_addr, data):
        self.from_addr = from_addr
        self.to_addr = to_addr
        self.data = data

    def hashify(self):
        return str(sha256(self.from_addr + self.to_addr + json.dumps(self.data)))

    def sign(self, key):
        if (key.get_verifying_key().to_string().hex() != self.from_addr):
            raise Exception("You do not own this Address.")
        hash = self.hashify()
        self.signature = key.sign(hash).hex()
        self.signature.to_der("hex")  # LOOK INTO


class Address:
    def __init__(self):
        self.ecdsa_key_pair = self.generateECDSAKeyPair()
        self.rsa_key_pair = self.generateRSAKeyPair()

    def generateECDSAKeyPair(self):
        private_key = SigningKey.generate(curve=SECP256k1)
        public_key = private_key.get_verifying_key()
        return {"private_key": private_key, "public_key": public_key}

    def getECDSAPrivateKey(self):
        return self.ecdsa_key_pair["private_key"].to_string().hex()

    def getECDSAPublicKey(self):
        return self.ecdsa_key_pair["public_key"].to_string().hex()

    def generateRSAKeyPair(self):
        (public_key, private_key) = rsa.newkeys(2048)
        return {"private_key": private_key, "public_key": public_key}

    def getRSAPrivateKey(self):
        return self.rsa_key_pair["private_key"].save_pkcs1(format="PEM").decode("utf-8")

    def getRSAPublicKey(self):
        return self.rsa_key_pair["public_key"].save_pkcs1(format="PEM").decode("utf-8")

    def generatePublicKeyTransaction(self):
        public_key_transaction = Mail(self.getECDSAPublicKey(), "0x0", self.getRSAPublicKey())
        public_key_transaction.sign(VerifyingKey.from_pem(self.ecdsa_key_pair["private_key"].to_pem().decode("utf-8")))
        return public_key_transaction


address_1 = Address()
print("ECDSA Private: " + address_1.getECDSAPrivateKey())
print("ECDSA Public: " + address_1.getECDSAPublicKey())
print(address_1.getRSAPrivateKey())
print(address_1.getRSAPublicKey())
