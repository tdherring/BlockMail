var active_masters = []


function checkNodeOnline(address) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        let node_request = {
            "action": "STILL_ALIVE"
        }
        socket.send(JSON.stringify(node_request));
    };
    socket.onmessage = function () {
        active_masters.push(address)
    };
}

function selectInNode() {
    return new Promise(function (resolve, reject) {
        for (x = 0; x < MASTER_NODES.length; x++) {
            checkNodeOnline(MASTER_NODES[x]);
        }
        let rand_node_index = Math.floor(Math.random() * active_masters.length);
        console.log(active_masters[rand_node_index]);

        setTimeout(function () {
            resolve(active_masters[rand_node_index]);
        }, 2000);
    });
}