const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");

$("#gen-keys-btn").click(function () {
    genECDSA();
    genRSA();
});

function genECDSA() {
    const ECDSA_KEY_PAIR = EC_INSTANCE.genKeyPair();
    const ECDSA_PUBLIC_KEY = ECDSA_KEY_PAIR.getPublic("hex");
    const ECDSA_PRIVATE_KEY = ECDSA_KEY_PAIR.getPrivate("hex");

    console.log("ECDSA Public Key: " + ECDSA_PUBLIC_KEY);
    console.log("ECDSA Private Key: " + ECDSA_PRIVATE_KEY);
}

function genRSA() {
    const RSA_KEY = new NODE_RSA({
        b: 2048
    });

    console.log("RSA Public Key: " + RSA_KEY.exportKey("public"));
    console.log("RSA Private Key: " + RSA_KEY.exportKey("private"));
}