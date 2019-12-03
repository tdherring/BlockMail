const MASTER_NODES = ["localhost:41286"];

function establishConnection() {
    for (var x = 0; x < MASTER_NODES.length; x++) {
        createSocket(MASTER_NODES[x]);
    }
}

function createSocket(address) {
    var socket = new WebSocket("ws://" + address, ["mail"]);
    socket.onopen = function() {
        console.log(getCookie("ecdsa_public"));
        socket.send(getCookie("ecdsa_public"));
    };
    socket.onmessage = function(event) {
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
