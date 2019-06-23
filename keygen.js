const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const KEY_PAIR = EC_INSTANCE.genKeyPair();
const PUBLIC_KEY = KEY_PAIR.getPublic("hex");
const PRIVATE_KEY = KEY_PAIR.getPrivate("hex");

console.log("\nPublic Key: " + PUBLIC_KEY);
console.log("Private Key: " + PRIVATE_KEY);

