const {Blockchain, Mail} = require("./blockchain");
const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");

//Generate an Address consisting of ECDSA (Address) and RSA (Mail Encryption) Key Pairs.
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

address_2 = new Address();
address_2_initiate = address_2.generatePublicKeyTransaction();
blockchain.addMail(address_2_initiate);

address_3 = new Address();
address_3_initiate = address_3.generatePublicKeyTransaction();
blockchain.addMail(address_3_initiate);

console.log("\nStarting Miner...");
blockchain.minePendingMail();

//Send an encrypted mail to addr2.
mail_3_to_2 = new Mail(address_3.getECDSAPublicKey(), address_2.getECDSAPublicKey(), new NODE_RSA(blockchain.getPublicKeyForAddress(address_2.getECDSAPublicKey())).encrypt("test", "base64"));
mail_3_to_2.sign(EC_INSTANCE.keyFromPrivate(address_3.getECDSAPrivateKey()));
blockchain.addMail(mail_3_to_2);

console.log("\nStarting Miner again...");
blockchain.minePendingMail();

// console.log("Mail for Address 1 - " + address_1.getECDSAPublicKey() + ":\n" + JSON.stringify(blockchain.getMailForAddress(address_1.getECDSAPublicKey()), null, 4));
// console.log("\nMail for Address 2 - " + address_2.getECDSAPublicKey() + ":\n" + JSON.stringify(blockchain.getMailForAddress(address_2.getECDSAPublicKey()), null, 4));
// console.log("\nMail for Address 3 - " + address_3.getECDSAPublicKey() + ":\n" + JSON.stringify(blockchain.getMailForAddress(address_3.getECDSAPublicKey()), null, 4)); 

console.log("\nEncrypted mail for Address 2: " + blockchain.getMailForAddress(address_2.getECDSAPublicKey())[1].data);
console.log("Decrypting mail for Address 2: " + address_2.rsa_key_pair.decrypt(blockchain.getMailForAddress(address_2.getECDSAPublicKey())[1].data));
console.log("Chain valid?: " + blockchain.validate());