$(function setup() {
    createNodeSocket(MASTER_NODES[0], "NODES_ON_NETWORK", null);
    createNodeSocket(MASTER_NODES[0], "CURRENT_BLOCK", null);
    $("#node-list").DataTable();
});

function createNodeSocket(address, request_type, table_id) {
    var socket = new WebSocket("ws://" + address);
    if (MASTER_NODES.includes(address)) {
        address = address + " [MASTER " + table_id + "]";
    }
    socket.onopen = function () {
        let node_request = {
            "action": request_type
        }
        socket.send(JSON.stringify(node_request));
    };
    socket.onerror = function () {
        if (request_type == "NODES_ON_NETWORK") {
            $(".wrapper").html("<h4>Unable to Connect to the BlockMail network. <a href='network-overview.html'>Try again?</a></h4>")
            $("#loading").addClass("hidden");
        } else {
            $("#node-li-" + table_id).removeClass("hidden");
            $('#node-list').DataTable().row.add([address, "<i class='fas fa-times-circle'>&zwnj;</i>", "-", "-"]).draw();
        }
    };
    socket.onmessage = function (event) {
        $("#loading").addClass("hidden");
        $("#overview-table").removeClass("hidden");
        if (request_type == "NODES_ON_NETWORK") {
            populateNodeList(JSON.parse(event.data).nodes_on_network);
        } else if (request_type == "CURRENT_BLOCK") {
            $("#current-block").html($("#current-block").html() + JSON.parse(event.data)["current_block"]);
        } else {
            let data = JSON.parse(event.data)
            $("#node-li-" + table_id).removeClass("hidden");
            if (data.known_nodes.length == 0) {
                $("#node-list").DataTable().row.add([address, "<i class='fas fa-check-circle'></i>", data.version, "None"]).draw();
            } else {
                $("#node-list").DataTable().row.add([address, "<i class='fas fa-check-circle'></i>", data.version, data.known_nodes.toString().split(",").join(", ")]).draw();
            }
        }
    };
}

function populateNodeList(nodes) {
    for (x = 0; x < nodes.length; x++) {
        createNodeSocket(nodes[x] + ":41286", "STILL_ALIVE", x);
    }
}