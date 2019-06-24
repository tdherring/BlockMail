const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const KEYPAIR = require("keypair");

const ECDSA_KEY_PAIR = EC_INSTANCE.genKeyPair();
const ECDSA_PUBLIC_KEY = ECDSA_KEY_PAIR.getPublic("hex");
const ECDSA_PRIVATE_KEY = ECDSA_KEY_PAIR.getPrivate("hex");

const RSA_KEY_PAIR = KEYPAIR();

console.log("ECDSA Public Key: " + ECDSA_PUBLIC_KEY);
console.log("ECDSA Private Key: " + ECDSA_PRIVATE_KEY);

console.log("\nRSA Public Key: " + RSA_KEY_PAIR.public);
console.log("RSA Public Key: " + RSA_KEY_PAIR.private);
