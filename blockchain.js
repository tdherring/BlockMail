const SHA256 = require("crypto-js/sha256");

//Block may have multiple Mail objects (Transactions).
class Mail {
    constructor(from_addr, to_addr, data) {
        this.from_addr = from_addr;
        this.to_addr = to_addr;
        this.data = data;
    }
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
        while(this.hash.substring(0, difficulty) != Array(difficulty + 1).join("0")) {
            this.nonce++;
            this.hash = this.hashify();
        }
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
        let block = new Block(Date.now(), this.pending_mail);
        block.mine(this.difficulty);
        console.log("Block Mined: " + block.hash);
        this.chain.push(block);
        this.pending_mail = [];
    }

    createMail(mail) {
        this.pending_mail.push(mail);
    }
    
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

    //Check that Blockchain integrity still good.
    validate() {
        for (let i = 1; i < this.chain.length; i++) {
            var current_block = this.chain[i];
            var previous_block = this.chain[i - 1];
            //If hash has changed, then Blockchain integrity disrupted.
            if (current_block.hash !== current_block.hashify()) {
                return false;
            }
            //If the previous_hash value in current block not equal to the previous blocks hash, integrity disrupted.
            if (current_block.previous_hash !== previous_block.hash) {
                return false;
            }
        }
        //Blockchain integrity must be good based on checks above.
        return true;
    }
}

module.export.Blockchain = Blockchain;
module.export.Mail = Mail;