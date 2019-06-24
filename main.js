const {Blockchain, Mail} = require("./blockchain");
const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");

class Address {
    constructor() {
        this.ecdsa_key_pair = this.generateECDSAKeyPair();
        this.rsa_key_pair = this.generateRSAKeyPair();
    }

    generateECDSAKeyPair() {
        return EC_INSTANCE.genKeyPair();
    }

    getECDSAPublicKey() {
        return this.ecdsa_key_pair.getPublic("hex");
    }

    getECDSAPrivateKey() {
        return this.ecdsa_key_pair.getPrivate("hex");
    }

    generateRSAKeyPair() {
        return new NODE_RSA({b: 2048});
    }

    getRSAPublicKey() {
        return this.rsa_key_pair.exportKey("public");
    }

    getRSAPrivateKey() {
        return this.rsa_key_pair.exportKey("private");
    }

    generatePublicKeyTransaction() {
        let public_key_transaction = new Mail(this.getECDSAPublicKey(), "0x0", this.getRSAPublicKey());
        public_key_transaction.sign(EC_INSTANCE.keyFromPrivate(this.getECDSAPrivateKey()));
        return public_key_transaction;
    }
}
blockchain = new Blockchain();
address_1 = new Address();
address_1_initiate = address_1.generatePublicKeyTransaction();
blockchain.addMail(address_1_initiate);

console.log("\nStarting Miner...");
blockchain.minePendingMail();

console.log("Mail for " + address_1.getECDSAPublicKey() + ":\n" + JSON.stringify(blockchain.getMailForAddress(address_1.getECDSAPublicKey()), null, 4));