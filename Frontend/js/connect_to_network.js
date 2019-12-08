const MASTER_NODES = ["127.0.0.1:41286", "127.0.0.2:41286", "127.0.0.3:41286", "127.0.0.4:41286"];

function establishConnection() {
    for (var x = 0; x < MASTER_NODES.length; x++) {
        createSocket(MASTER_NODES[x]);
    }
}

function createSocket(address) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        let email_data = {
            "action": "SEND",
            "send_addr": getCookie("ecdsa_public"),
            "recv_addr": null,
            "subject": null,
            "body": null
        }
        socket.send(JSON.stringify(email_data));
    };
    socket.onmessage = function (event) {
        console.log(event.data);
    };
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

establishConnection();