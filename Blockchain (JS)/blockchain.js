const SHA256 = require("crypto-js/sha256");
const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");

//Block may have multiple Mail objects (Transactions).
class Mail {
    constructor(from_addr, to_addr, data) {
        this.from_addr = from_addr;
        this.to_addr = to_addr;
        this.data = data;
    }

    //Generate the hash of the mail using SHA256.
    hashify() {
        return SHA256(this.from_addr + this.to_addr + JSON.stringify(this.data)).toString();
    }

    //Set the signature of the Mail.
    sign(key) {
        //If hash not correct, then do not authenticate and throw error.
        if (key.getPublic("hex") !== this.from_addr) {
            throw new Error("You do not own this Address.");
        }
        let hash = this.hashify();
        let signature = key.sign(hash, "base64");
        this.signature = signature.toDER("hex");
    }

    //Check the mail has been signed correctly.
    validate() {
        if (!this.signature || this.signature.length === 0) {
            throw new Error("This Mail has not been signed.");
        }
        let public_key = EC_INSTANCE.keyFromPublic(this.from_addr, "hex");
        return public_key.verify(this.hashify(), this.signature);
    }

    //Encrypts the data of the mail (body, optional from, etc) which would otherwise be viewable by anyone with the wallet address.
     
}

//Blocks comprise the Blockchain.
class Block {
    constructor(timestamp, mail, previous_hash = "") {
        this.timestamp = timestamp;
        this.mail = mail;
        this.nonce = 0; //Facilitates mining by changing hash on each block mine iteration. See https://en.bitcoin.it/wiki/Nonce.
        this.previous_hash = previous_hash;
        this.hash = this.hashify();
    }

    //Calculate the hash of the Block using SHA256.
    hashify() {
        return SHA256(this.timestamp + JSON.stringify(this.mail) + this.nonce+ this.previous_hash).toString();
    }

    //Mine a block of given difficulty.
    mine(difficulty) {
        while(this.hash.substring(0, difficulty) !== Array(difficulty + 1).join("0")) {
            this.nonce++;
            this.hash = this.hashify();
        }
    }

    //Check that all mail in block is valid.
    validateAllMail() {
        //Iterate through each object of mail array, and call validate() on it.
        for (var mail of this.mail) {
            if (mail.validate() === false) {
                return false
            }
        }
        //Based on checks above, all mail in block must be valid.
        return true;
    }
}

//The primary data structure that contains all blocks.
class Blockchain {
    constructor() {
        this.chain = [this.createGenesis()];
        this.difficulty = 2;
        this.pending_mail = [];
    }

    //Create the Genesis block.
    createGenesis() {
        return new Block("22/06/2019 00:00:00", "Genesis", "0");
    }

    //Return the last block in the Blockchain.
    getLastBlock() {
        return this.chain[this.chain.length - 1];
    }
    
    //Mine all mail in queue.
    minePendingMail() {
        let block = new Block(Date.now(), this.pending_mail, this.chain[this.chain.length-1].hashify());
        block.mine(this.difficulty);
        console.log("Block Mined: " + block.hash);
        this.chain.push(block);
        this.pending_mail = [];
    }

    //Add Mail object to end of queue (send).
    addMail(mail) {
        if (!mail.from_addr || !mail.to_addr) {
            throw new Error("No From or To address given.");
        }
        if (mail.validate() === false) {
            throw new Error("Mail signature invalid. Cannot add to pending mail queue.");
        }
        this.pending_mail.push(mail);
    }
    
    //Return all mail associated with address.
    getMailForAddress(addr) {
        let mail_for_addr = [];
        for (var block of this.chain) {
            for (var mail of block.mail) {
                if (mail.from_addr == addr || mail.to_addr == addr) {
                    mail_for_addr.push(mail);
                }
            }
        }
        return mail_for_addr;
    }

    getPublicKeyForAddress(addr) {
        for (var block of this.chain) {
            for (var mail of block.mail) {
                if (mail.from_addr == addr) {
                    return mail.data;
                }
            }
        }
        return null;
    }

    //Check that Blockchain integrity still good.
    validate() {
        for (let i = 1; i < this.chain.length; i++) {
            var current_block = this.chain[i];
            var previous_block = this.chain[i - 1];
            //If mail in current block not valid, integrity disrupted -OR-
            //If hash has changed, then Blockchain integrity disrupted -OR-
            //If the previous_hash value in current block not equal to the previous blocks hash, integrity disrupted.
            if (current_block.validateAllMail() === false || current_block.hash !== current_block.hashify() || current_block.previous_hash !== previous_block.hashify()) {
                return false;
            }
        }
        //Blockchain integrity must be good based on checks above.
        return true;
    }
}

module.exports.Blockchain = Blockchain;
module.exports.Mail = Mail;