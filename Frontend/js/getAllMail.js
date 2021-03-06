/**
 * Called on DOM load. Gets all nodes on the network.
 * Also converts email-list to a DataTable.
 */
$(function setup() {
    selectInNode().then(function (result) {
        createMailSocket(result, "NODES_ON_NETWORK", null);
    });
    $("#email-list").DataTable();
});

/**
 * Creates a mail socket with the given node and gets all mail from that node.
 * @param {*} address The address of the BlockMail node to connect to.
 */
function createMailSocket(address) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        let get_request = {
            "action": "GET",
            "wallet_public": "*",
        };
        socket.send(JSON.stringify(get_request));
    };
    socket.onmessage = function (event) {
        $("#loading").addClass("hidden");
        $("#overview-table").removeClass("hidden");
        populateEmailList(JSON.parse(event.data)["emails"]);
    };
}

/**
 * Populates the email table with the required data. 
 * @param {*} emails The JSON of all mail on the network.
 */
function populateEmailList(emails) {
    $("#email-list").append("<tbody>");
    for (x = emails.length - 1; x >= 0; x--) {
        let datetime = new Date(Date.parse(emails[x]["datetime"]));
        $("#email-list").DataTable().row.add(["<span class='word-wrap'>" + emails[x]["mail_hash_digest"] + "</span>", emails[x]["origin_node"], "<span class='word-wrap'>" + emails[x]["send_addr"] + "</span>", "<span class='word-wrap'>" + emails[x]["recv_addr"] + "</span>", emails[x]["block"], datetime.toLocaleDateString() + ", " + datetime.toLocaleTimeString()]).draw();
    }
    $("#email-list").DataTable().order([4, "desc"]).draw();
    $("#email-list").append("</tbody>");
}