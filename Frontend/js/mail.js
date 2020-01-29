const MASTER_NODES = ["127.0.0.1:41286", "127.0.0.2:41286", "127.0.0.3:41286", "127.0.0.4:41286"];

function createSocket(address, mail) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        if (mail != null) { // Send
            socket.send(JSON.stringify(mail));
        } else {
            let public_key = getCookie("ecdsa_public");
            let get_request = {
                "action": "GET",
                "public_key": public_key,
            }
            socket.send(JSON.stringify(get_request));
        }
    };
    socket.onmessage = function (event) {
        console.log(event.data);
    };
}

function sendMail(mail) {
    createSocket(MASTER_NODES[0], mail) // Will randomize later.
}

function getMail() {
    createSocket(MASTER_NODES[0], null)
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

$(".send-email-form").submit(function sendEmail() {
    let public_key = getCookie("ecdsa_public");
    let private_key = getCookie("ecdsa_private");
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

    sendMail(mail);
});

$(getMail()); // Retrieve mail on load of DOM.