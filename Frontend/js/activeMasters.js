var active_masters = []

/**
 * Checks whether a node is alive and running.
 * @param {*} address The address of the BlockMail node to connect to.
 */
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

/**
 * A promise which finds nodes available for connection.
 */
function selectInNode() {
    return new Promise(function (resolve, reject) {
        for (x = 0; x < MASTER_NODES.length; x++) {
            checkNodeOnline(MASTER_NODES[x]);
        }
        let rand_node_index = Math.floor(Math.random() * active_masters.length);

        setTimeout(function () {
            resolve(active_masters[rand_node_index]);
        }, 2000);
    });
}