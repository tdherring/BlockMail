const MASTER_NODES = ["127.0.0.1:41286", "127.0.0.2:41286", "127.0.0.3:41286", "127.0.0.4:41286"];
const NODE_RSA = require("node-rsa");
var mobile = false;
var page_counter = 0;

/* Retrieve mail on load of DOM. */
$(setTimeout(function setup() {
    $(window).delay(1000);
    if (getCookie("ecdsa_public") == "") {
        window.location = "login.html";
    } else {
        createSocket(MASTER_NODES[0], "GET", null);
        $(window).resize();
    }
}, 1000));

/* Listen for new send mail object. Package mail, and pass to encrypt() method for processing. */
$("#send-email-form").submit(function (e) {
    e.preventDefault(); // Prevent reload.
    createSocket(MASTER_NODES[0], "KEY", null)
});

$("#compose-btn").click(function () {
    $("#mail-placeholder").addClass("hidden");
    $("#send-email-form").removeClass("hidden");
    if (mobile) {
        $("#email-outer-col").addClass("hidden");
        $("#compose-btn").parent().addClass("hidden");
        $("#back-btn").parent().removeClass("hidden");
        $("#decrypt-btn").parent().addClass("hidden");
        $("#send-email-form").parent().removeClass("col-7");
        $("#send-email-form").parent().addClass("col-12");
    } else {
        $("#mail-view").addClass("hidden");
    }
});

$("#decrypt-btn").click(function () {
    $("#decrypt-modal").modal();
});

$("#private-key-file").change(function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        $("#private-key").val(event.target.result);
    }
    reader.onerror = error => reject(error);
    reader.readAsText(this.files[0]);
    $("#private-key-file-label").addClass("hidden");
    $("#clear-private").removeClass("hidden");
});

$("#clear-private").click(function () {
    $("#private-key").val("");
    $("#private-key-file").val("");
    $("#private-key-file-label").removeClass("hidden");
    $("#or-tag").removeClass("hidden");
    $("#clear-private").addClass("hidden");
});

$("#decrypt-form").submit(function (e) {
    if ($("#private-key").val() == "") {
        if ($(".alert").length > 0) {
            $(".alert").html("You must enter or upload a key to decrypt with. ");
        } else {
            $(".modal-body").append(
                `<div class='alert alert-danger' role='alert'>
                    You must enter or upload a key to decrypt with.
                </div>`);
        }
    } else {
        e.preventDefault(); // Prevent reload.
        console.log($("#private-key").val());
        let key_pair = new NODE_RSA($("#private-key").val());
        for (let x = 0; x < mail_json.length; x++) {
            let decrypted_subject = key_pair.decrypt(mail_json[x].subject, "utf8");
            let decrypted_body = key_pair.decrypt(mail_json[x].body, "utf8");
            mail_json[x].subject = decrypted_subject;
            mail_json[x].body = decrypted_body;
            if (x < 5) {
                $("#email-obj-subject-" + x).html(decrypted_subject);
                $("#email-obj-body-" + x).html(decrypted_body);
            }
        }
    }
});

/* Listen for resize event. Adjust elements to display correctly. */
$(window).resize(function checkSize() {
    if ($(document).width() < 1555) {
        mobile = true;
        $("#compose-btn").parent().removeClass("col-2");
        $("#compose-btn").parent().addClass("col-6");
        $("#decrypt-btn").parent().removeClass("col-2");
        $("#decrypt-btn").parent().addClass("col-6");
        $("#email-outer-col").removeClass("col-5");
        $("#email-outer-col").addClass("col-12");
        if ($("#mail-view").hasClass("hidden")) {
            $("#mail-placeholder").addClass("hidden");
        }
        if (!$("#send-email-form").hasClass("hidden") || !$("#mail-view").hasClass("hidden")) {
            $("#send-email-form").parent().removeClass("col-7");
            $("#send-email-form").parent().addClass("col-12");
            $("#email-outer-col").addClass("hidden");
            $("#back-btn").parent().removeClass("hidden");
            $("#compose-btn").parent().addClass("hidden");
            $("#decrypt-btn").parent().addClass("hidden");
        }
    } else {
        mobile = false;
        $("#back-btn").parent().addClass("hidden");
        $("#compose-btn").parent().removeClass("hidden");
        $("#decrypt-btn").parent().removeClass("hidden");
        $("#compose-btn").parent().removeClass("col-6");
        $("#compose-btn").parent().addClass("col-2");
        $("#decrypt-btn").parent().removeClass("col-6");
        $("#decrypt-btn").parent().addClass("col-2");
        $("#email-outer-col").addClass("col-5");
        $("#email-outer-col").removeClass("col-12");
        $("#mail-view").parent().removeClass("col-12");
        $("#mail-view").parent().addClass("col-7");
        if ($("#mail-view").hasClass("hidden")) {
            $("#email-outer-col").removeClass("col-12");
            $("#mail-placeholder").removeClass("hidden");
            $("#decrypt-btn").parent().removeClass("hidden");
        }
        if (!$("#send-email-form").hasClass("hidden") || !$("#mail-view").hasClass("hidden")) {
            $("#email-outer-col").removeClass("hidden");
            $("#send-email-form").parent().removeClass("col-12");
            $("#send-email-form").parent().addClass("col-7");
            $("#mail-placeholder").addClass("hidden");
        }
    }
});

/* Establish a WebSocket connection to the given address.
    Arguments:
        mail - The JSON mail object containing the body and subject to be encrypted using the recipient's public key.
*/
function encrypt(mail, keys) {
    let keys_json = JSON.parse(keys);
    console.log(keys_json)
    let recipient_public_key = new NODE_RSA(keys_json["recv_key"]);
    let sender_public_key = new NODE_RSA(keys_json["send_key"]);
    mail["subject_receiver"] = recipient_public_key.encrypt(mail["subject"], "base64");
    mail["subject_sender"] = sender_public_key.encrypt(mail["subject"], "base64");
    mail["body_receiver"] = recipient_public_key.encrypt(mail["body"], "base64");
    mail["body_sender"] = sender_public_key.encrypt(mail["body"], "base64");
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
                "recv_addr": $("#to").val(),
                "send_addr": getCookie("ecdsa_public")
            }
            socket.send(JSON.stringify(key_request));
        }
    };
    socket.onerror = function () {
        $(".wrapper").append("<h4>Unable to Connect to the BlockMail network. <a href='mail.html'>Try again?</a></h4>")
        $("#loading").addClass("hidden");
    };
    socket.onmessage = function (event) {
        if (request_type == "SEND") {
            //do something
        } else if (request_type == "GET") {
            $("#loading").addClass("hidden");
            $("#mail-wrapper").removeClass("hidden");
            writeMailToDom(event.data);
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

function writeMailToDom(mail) {
    mail_json = JSON.parse(mail).emails;
    console.log(mail_json);
    for (let x = 0; x < 5; x++) {
        changePage(page_counter, mail_json);
    }
    monitorPageChange();
}


function monitorPageChange() {
    $("#prev-page").unbind().click(function prevPage() {
        if (page_counter != 0) {
            page_counter -= 1;
            changePage(page_counter, mail_json);
        }
    });

    $("#next-page").unbind().click(function nextPage() {
        if ((page_counter + 1) * 5 < mail_json.length) {
            page_counter += 1;
            changePage(page_counter, mail_json)
        }
    });
}

function changePage(page_counter, mail_json) {
    let start_index = page_counter * 5;
    let end_index = start_index + 5;
    $("#email-table").empty();
    $("#page-num").html(page_counter + 1);
    for (let x = start_index; x < end_index; x++) {
        try {
            $("#email-table").append(
                `<tr>
                <td>
                    <a id="email-obj-` + x + `" href="#">
                        <h4 id="email-obj-subject-` + x + `">` + mail_json[x].subject + `</h4>
                        <h5>From: ` + mail_json[x].send_addr + `</h5>
                        <h6 id="email-obj-body-` + x + `">` + mail_json[x].body + `</h6>
                        <em>` + mail_json[x].datetime + `</em>
                    </a>
                </td>
            </tr> `);
        } catch {
            $("#email-table").append(
                `<tr>
                <td>
                </td>
            </tr> `);
        }
    }
    monitorEmailClick();
    monitorBackClick(mail_json);
}

function monitorEmailClick() {
    $("[id^=email-obj-]").click(function viewEmail(event) {
        let mail_index = event.currentTarget.id.slice(10);
        let mail_to_show = mail_json[mail_index];
        $("#mail-view-subject").html(mail_to_show.subject);
        $("#mail-view-from").html(mail_to_show.send_addr);
        $("#mail-view-datetime").html(mail_to_show.datetime);
        $("#mail-view-body").html(mail_to_show.body);
        $("#mail-view").removeClass("hidden");
        if (mobile) {
            $("#email-outer-col").addClass("hidden");
            $("#back-btn").parent().removeClass("hidden");
            $("#compose-btn").parent().addClass("hidden");
            $("#decrypt-btn").parent().addClass("hidden");
            $("#mail-view").parent().removeClass("col-7");
            $("#mail-view").parent().addClass("col-12");
        } else {
            $("#mail-placeholder").addClass("hidden");
            $("#send-email-form").addClass("hidden");
        }
    });
}

function monitorBackClick(mail_json) {
    $("#back-btn").click(function () {
        $("#decrypt-btn").parent().removeClass("hidden");
        $("#compose-btn").parent().removeClass("hidden");
        $("#send-email-form").addClass("hidden");
        $("#email-outer-col").removeClass("hidden");
        monitorPageChange();
        $("#mail-view").addClass("hidden");
        $("#compose-btn").parent().removeClass("hidden");
        $("#back-btn").parent().addClass("hidden");
        changePage(page_counter, mail_json);
    });
}

/* Select a node at Random as an entry point to the network. */
function pickEntryPoint() {
    let random = Math.floor(Math.random() * Math.floor(MASTER_NODES.length));
    return MASTER_NODES[random];
}