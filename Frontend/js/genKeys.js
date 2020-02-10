const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");
const MASTER_NODES = ["127.0.0.1:41286", "127.0.0.2:41286", "127.0.0.3:41286", "127.0.0.4:41286"];

$("#gen-keys-btn").click(function () {
    $("#keys").empty(); // Clear current key-gen if exists.
    let ecdsa = genECDSA();
    let rsa = genRSA();
    writeToBlockchain(MASTER_NODES[0], rsa["public"], ecdsa["public"]);
});

function writeToBlockchain(address, rsa_public_key, ecdsa_public_key) {
    let key_obj = {
        "action": "SEND",
        "send_addr": ecdsa_public_key,
        "recv_addr": "0x0",
        "subject_sender": "**RSA-PUBLIC**",
        "subject_receiver": "",
        "body_sender": rsa_public_key,
        "body_receiver": ""
    }
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        socket.send(JSON.stringify(key_obj));
    };
}


function genECDSA() {
    let ecdsa_key_pair = EC_INSTANCE.genKeyPair(); // Generate ECDSA SECP256K1 key pair.
    let ecdsa_public_key = ecdsa_key_pair.getPublic("hex"); //Extract public key.
    let ecdsa_private_key = ecdsa_key_pair.getPrivate("hex"); //Extract private key.

    $("#keys").append("<br><hr><h6>Wallet Address</h6>" + ecdsa_public_key + "<input id='download-ecdsa-public' type='button' class='btn btn-lg btn-dark btn-primary btn-block text-uppercase download-btn' value='Download'></button>")
    $("#download-ecdsa-public").click(function () { //Wait for download click.
        downloadFile(ecdsa_public_key, "wallet.addr");
    });

    $("#keys").append("<h6>Wallet Password</h6>" + ecdsa_private_key + "<input id='download-ecdsa-private' type='button' class='btn btn-lg btn-dark btn-primary btn-block text-uppercase download-btn' value='Download'></button>")
    $("#download-ecdsa-private").click(function () {
        downloadFile(ecdsa_private_key, "wallet.pass")
    });

    return {
        "public": ecdsa_public_key,
        "private": ecdsa_private_key
    }
}

function genRSA() {
    let rsa_key = new NODE_RSA({ // Generate RSA key pair with 2048 bit key.
        b: 2048
    });
    let rsa_public_key = rsa_key.exportKey("public");
    let rsa_private_key = rsa_key.exportKey("private");

    $("#keys").append("<h6>Mail Decryption Key</h6>" + rsa_private_key + "<input id='download-rsa-private' type='button' class='btn btn-lg btn-dark btn-primary btn-block text-uppercase download-btn' value='Download'></button>")
    $("#download-rsa-private").click(function () {
        downloadFile(rsa_private_key, "private.key")
    });

    return {
        "public": rsa_public_key,
        "private": rsa_private_key
    };
}


function downloadFile(data, name) {
    let a = document.createElement('a');
    a.href = "data:application/octet-stream," + encodeURIComponent(data);
    a.download = name;
    a.click();
}