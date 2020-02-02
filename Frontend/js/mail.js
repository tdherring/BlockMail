const MASTER_NODES = ["127.0.0.1:41286", "127.0.0.2:41286", "127.0.0.3:41286", "127.0.0.4:41286"];
const NODE_RSA = require("node-rsa");

/* Retrieve mail on load of DOM. */
$(createSocket(MASTER_NODES[0], "GET", null));

/* Listen for new send mail object. Package mail, and pass to encrypt() method for processing. */
$(".send-email-form").submit(function sendEmail(e) {
    e.preventDefault(); // Prevent reload.

    createSocket(MASTER_NODES[0], "KEY", null)
});

/* Establish a WebSocket connection to the given address.
   Arguments:
       mail - The JSON mail object containing the body and subject to be encrypted using the recipient's public key.
*/
function encrypt(mail, key) {
    let rsa_key_json = JSON.parse(key);
    let recipient_public_key = new NODE_RSA(rsa_key_json["key"]);
    mail["subject"] = recipient_public_key.encrypt(mail["subject"], "base64");
    mail["body"] = recipient_public_key.encrypt(mail["body"], "base64");
    createSocket(MASTER_NODES[0], "SEND", mail) // Will randomize later.
}

/* Establish a WebSocket connection to the given address.
   Arguments:
       address - The node address to send the mail to. This is the entry point to the BlockMail network.
       request_type - GET, SEND, KEY. Identifies what the purpose of the socket is.
       encrypted_mail - Contains the mail object, including encrypted body / subject. If null, request is GET mail. 
*/
function createSocket(address, request_type, encrypted_mail) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        if (request_type == "SEND") { // Send
            socket.send(JSON.stringify(encrypted_mail));
        } else if (request_type == "GET") {
            let wallet_public = getCookie("ecdsa_public");
            let get_request = {
                "action": "GET",
                "wallet_public": wallet_public,
            };
            socket.send(JSON.stringify(get_request));
        } else if (request_type == "KEY") {
            let key_request = {
                "action": "KEY",
                "recv_addr": $("#to").val()
            }
            socket.send(JSON.stringify(key_request));
        }
    };
    socket.onmessage = function (event) {
        if (request_type == "SEND") {
            //do something
        } else if (request_type == "GET") {
            //do something 
        } else if (request_type == "KEY") {
            let public_key = getCookie("ecdsa_public");
            let to = $("#to").val();
            let subject = $("#subject").val();
            let body = $("#body").val();

            let mail = {
                "action": "SEND",
                "send_addr": public_key,
                "recv_addr": to,
                "subject": subject,
                "body": body,
            }

            encrypt(mail, event.data);
        }
        return event.data;
    };
}

/* Select a node at Random as an entry point to the network. */
function pickEntryPoint() {
    let random = Math.floor(Math.random() * Math.floor(MASTER_NODES.length));
    return MASTER_NODES[random];
}

function getCookie(cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(";");
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == " ") {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}