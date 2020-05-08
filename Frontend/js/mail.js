const NODE_RSA = require("node-rsa");
var mobile = false;
var page_counter = 0;

/** 
 * Retrieve mail on load of DOM. 
 * */
$(setTimeout(function setup() {
    $(window).delay(1000);
    if (getCookie("ecdsa_public") == "") {
        window.location = "login.html";
    } else {
        selectInNode().then(function (result) {
            in_node = result;
            createSocket(in_node, "GET", null);
        });
        $(window).resize();
    }
}, 1000));

/**
 *  Listen for new send mail object. Package mail, and pass to encrypt() method for processing. #
 * */
$("#send-email-form").submit(function (e) {
    e.preventDefault(); // Prevent reload.
    createSocket(in_node, "KEY", null)
});

/**
 * Listen for press of "compose" button.
 */
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

/**
 * Listen for press of "decrypt" button.
 */
$("#decrypt-btn").click(function () {
    $("#decrypt-modal").modal();
});

/**
 * Listen for change of the private key input field in the decryption dialog.
 */
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

/**
 * Listen for press of the "clear" button in the decryption dialog.
 */
$("#clear-private").click(function () {
    $("#private-key").val("");
    $("#private-key-file").val("");
    $("#private-key-file-label").removeClass("hidden");
    $("#or-tag").removeClass("hidden");
    $("#clear-private").addClass("hidden");
});

/**
 * Wait for submission of the decryption form.
 */
$("#decrypt-form").submit(function (e) {
    e.preventDefault(); // Prevent reload.
    if ($("#private-key").val() == "") {
        if ($(".alert").length > 0) {
            $(".alert").html("You must enter or upload a key to decrypt with.");
        } else {
            $(".modal-body").append(
                `<div class='alert alert-danger' role='alert'>
                    You must enter or upload a key to decrypt with.
                </div>`);
        }
    } else {
        let key_pair = new NODE_RSA($("#private-key").val());
        for (let x = 0; x < mail_json.length; x++) {
            try {
                let decrypted_subject = key_pair.decrypt(mail_json[x]["subject"], "utf8");
                let decrypted_body = key_pair.decrypt(mail_json[x]["body"], "utf8");
                mail_json[x]["subject"] = decrypted_subject;
                mail_json[x]["body"] = decrypted_body;
                if (x < 5) {
                    $("#email-obj-subject-" + x).html(decrypted_subject);
                    $("#email-obj-body-" + x).html(decrypted_body);
                }
                if ($(".alert-success").length == 0) {
                    $(".modal-body").append(
                        `<div class='alert alert-success' role='alert'>
                        Decryption successful!
                    </div>`);
                }
            } catch {
                if ($(".alert").length > 0) {
                    $(".alert").html("Decryption failed. Please try again with the correct key.");
                } else {
                    $(".modal-body").append(
                        `<div class='alert alert-danger' role='alert'>
                            Decryption failed. Please try again with the correct key.
                        </div>`);
                }
            }
        }
    }
});

/**
 * Listen for resize event. Adjust elements to display correctly. 
 * */
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

/**
 * Establish a WebSocket connection to the given address.
 * @param {*} mail The JSON mail object to be encrypted.
 * @param {*} keys_json The JSON of the sender and recipient public key.
 */
function encrypt(mail, keys_json) {
    let recipient_public_key = new NODE_RSA(keys_json["recv_key"]);
    let sender_public_key = new NODE_RSA(keys_json["send_key"]);
    mail["subject_receiver"] = recipient_public_key.encrypt(mail["subject"], "base64");
    mail["subject_sender"] = sender_public_key.encrypt(mail["subject"], "base64");
    mail["body_receiver"] = recipient_public_key.encrypt(mail["body"], "base64");
    mail["body_sender"] = sender_public_key.encrypt(mail["body"], "base64");
    createSocket(in_node, "SEND", mail) // Will randomize later.
}

/**
 * Establish a WebSocket connection to the given address.
 * @param {*} address The node address to send the mail to. This is the entry point to the BlockMail network.
 * @param {*} request_type GET, SEND, KEY. Identifies what the purpose of the socket is.
 * @param {*} encrypted_mail Contains the mail object, including encrypted body / subject. If null, request is GET mail. 
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
            $("#mail-modal-title").html("Mail Sent!");
            $("#mail-modal-body").html("Your email has been sent! It should appear in the recipients mailbox at the next Block interval.");
            $("#mail-modal").modal();
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
            let data = JSON.parse(event.data);
            if (data["recv_key"] === undefined) {
                $("#mail-modal-title").html("Address Not Found");
                $("#mail-modal-body").html("The address specified was not found in the BlockMail network. It may be of the wrong format. Please check your input and try again.");
                $("#mail-modal").modal();
            } else {
                encrypt(mail, data);
            }
        }
        return event.data;
    };
}

/**
 * Puts the emails on the page.
 * @param {*} mail The JSON object containing all emails.
 */
function writeMailToDom(mail) {
    mail_json = JSON.parse(mail).emails;
    for (let x = 0; x < 5; x++) {
        getCurrentBlock(page_counter, mail_json, in_node)
    }
    monitorPageChange();
}

/**
 * Wait for user to click "next" or "prev" and adjust view accordingly.
 */
function monitorPageChange() {
    $("#prev-page").unbind().click(function prevPage() {
        if (page_counter != 0) {
            page_counter -= 1;
            getCurrentBlock(page_counter, mail_json, in_node)
        }
    });

    $("#next-page").unbind().click(function nextPage() {
        if ((page_counter + 1) * 5 < mail_json.length) {
            page_counter += 1;
            getCurrentBlock(page_counter, mail_json, in_node)
        }
    });
}

/**
 * Rewrites the DOM with the correct objects.
 * @param {*} page_counter The current page index.
 * @param {*} mail_json A JSON object of all mail.
 * @param {*} current_block The name of the current block.
 */
function changePage(page_counter, mail_json, current_block) {
    let start_index = page_counter * 5;
    let end_index = start_index + 5;
    $("#email-table").empty();
    $("#page-num").html(page_counter + 1);
    for (let x = start_index; x < end_index; x++) {
        try {
            let datetime = new Date(mail_json[x]["datetime"]);
            let formatted_datetime = datetime.toLocaleDateString() + ", " + datetime.toLocaleTimeString();
            if (mail_json[x].send_addr == getCookie("ecdsa_public")) {
                $("#email-table").append(
                    `<tr>
                        <td>
                            <a id="email-obj-` + x + `" href="#">
                                <h4  class='col-12' id="email-obj-subject-` + x + `">` + mail_json[x].subject + `</h4>
                                <h5 class='col-12'>To:` + mail_json[x].recv_addr + `</h5>
                                <h6 class='col-12' id="email-obj-body-` + x + `">` + mail_json[x].body + `</h6>
                                <em class='col-3'>` + formatted_datetime + `, ` + (current_block - mail_json[x].block.substring(1)) + ` Confirmations</em>
                            </a>
                        </td>
                    </tr> `);
            } else {
                $("#email-table").append(
                    `<tr>
                        <td>
                            <a id="email-obj-` + x + `" href="#">
                                <h4 class='col-12' id="email-obj-subject-` + x + `">` + mail_json[x].subject + `</h4>
                                <h5 class='col-12'>From:` + mail_json[x].send_addr + `</h5>
                                <h6 class='col-12' id="email-obj-body-` + x + `">` + mail_json[x].body + `</h6>
                                <em class='col-3'>` + formatted_datetime + `, ` + (current_block - mail_json[x].block.substring(1)) + ` Confirmations</em>
                            </a>
                        </td>
                    </tr> `);
            }
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

/**
 * Requests the current block form a node.
 * @param {*} page_counter The current page index.
 * @param {*} mail_json A JSON object of all mail.
 * @param {*} address The node address.
 */
function getCurrentBlock(page_counter, mail_json, address) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        let get_request = {
            "action": "CURRENT_BLOCK",
        };
        socket.send(JSON.stringify(get_request));
    };
    socket.onmessage = function (event) {
        json = JSON.parse(event.data);
        changePage(page_counter, mail_json, json.current_block.substring(1));
    };
}

/**
 * Wait for user to click email and display on screen.
 */
function monitorEmailClick() {
    $("[id^=email-obj-]").click(function viewEmail(event) {
        let mail_index = event.currentTarget.id.slice(10);
        let mail_to_show = mail_json[mail_index];
        let datetime = new Date(mail_to_show["datetime"]);
        let formatted_datetime = datetime.toLocaleDateString() + ", " + datetime.toLocaleTimeString();
        $("#mail-view-subject").html(mail_to_show.subject);
        if (mail_to_show.send_addr == getCookie("ecdsa_public")) {
            $("#mail-view-from").html("To:" + mail_to_show["recv_addr"]);
        } else {
            $("#mail-view-from").html("From:" + mail_to_show["send_addr"]);
        }
        $("#mail-view-datetime").html(formatted_datetime);
        $("#mail-view-body").html(mail_to_show["body"]);
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

/**
 * Wait for press of "back" button.
 */
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
        getCurrentBlock(page_counter, mail_json, in_node)
    });
}