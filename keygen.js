const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");

const ECDSA_KEY_PAIR = EC_INSTANCE.genKeyPair();
const ECDSA_PUBLIC_KEY = ECDSA_KEY_PAIR.getPublic("hex");
const ECDSA_PRIVATE_KEY = ECDSA_KEY_PAIR.getPrivate("hex");

const RSA_KEY = new NODE_RSA({b: 2048});
const RSA_KEY2 = new NODE_RSA({b: 2048});

console.log("ECDSA Public Key: " + ECDSA_PUBLIC_KEY);
console.log("ECDSA Private Key: " + ECDSA_PRIVATE_KEY);

console.log("\n" + RSA_KEY.exportKey("public"));
console.log("\n" + RSA_KEY.exportKey("private"));

var data_to_encrypt = "hello";

var encrypted_data = RSA_KEY.encrypt(data_to_encrypt, "base64");
console.log("\nEncrypted data:\n" + encrypted_data);

var decrypted_data = RSA_KEY.decrypt(encrypted_data);
console.log("\nDecrypted data:\n" + decrypted_data);

// var fail_decrypt = RSA_KEY2.decrypt(encrypted_data);
// console.log("\nFail Decrypt:\n" + fail_decrypt);

//Generates the Mail Account (Address).
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

    publishPublicKey() {
        let pub_key_transaction = new Mail(this.getECDSAPublicKey(), "0x0", this.getRSAPublicKey());
    }
}