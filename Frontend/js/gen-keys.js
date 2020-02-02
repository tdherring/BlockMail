const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");
const NODE_RSA = require("node-rsa");

$("#gen-keys-btn").click(function () {
    $("#keys").empty(); // Clear current key-gen if exists.
    genECDSA();
    genRSA();
});

function genECDSA() {
    let ecdsa_key_pair = EC_INSTANCE.genKeyPair(); // Generate ECDSA SECP256K1 key pair.
    let ecdsa_public_key = ecdsa_key_pair.getPublic("hex"); //Extract public key.
    let ecdsa_private_key = ecdsa_key_pair.getPrivate("hex"); //Extract private key.

    $("#keys").append("<br><hr><h6>Wallet Address</h6>" + ecdsa_public_key + "<button class='btn btn-lg btn-primary btn-block text-uppercase download-btn'>Download</button>")
    $("#download-ecdsa-public").click(function () { //Wait for download click.
        downloadFile(ecdsa_public_key, "wallet.addr");
    });

    $("#keys").append("<h6>Wallet Password</h6>" + ecdsa_private_key + "<button class='btn btn-lg btn-primary btn-block text-uppercase download-btn'>Download</button>")
    $("#download-ecdsa-private").click(function () {
        downloadFile(ecdsa_private_key, "wallet.pass")
    });
}

function genRSA() {
    let rsa_key = new NODE_RSA({ // Generate RSA key pair with 2048 bit key.
        b: 2048
    });
    let rsa_public_key = rsa_key.exportKey("public");
    let rsa_private_key = rsa_key.exportKey("private");

    $("#keys").append("<h6>Mail Decryption Key</h6>" + rsa_private_key + "<button class='btn btn-lg btn-primary btn-block text-uppercase download-btn'>Download</button>")
    $("#download-rsa-private").click(function () {
        downloadFile(rsa_private_key, "private.key")
    });
}

function downloadFile(data, name) {
    let a = document.createElement('a');
    a.href = "data:application/octet-stream," + encodeURIComponent(data);
    a.download = name;
    a.click();
}