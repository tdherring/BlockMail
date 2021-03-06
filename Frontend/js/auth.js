const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");



/**
 *  Handle initial "Authenticate" button press. 
 */
$("#auth-btn").click(function () {
    //Get values of login form fields into variables.
    var ecdsa_public_text = $("#ecdsa-public").val();
    var ecdsa_private_text = $("#ecdsa-private").val();

    if (checkECDSAKey(ecdsa_public_text, true) && checkECDSAKey(ecdsa_private_text, false)) {
        selectInNode().then(function (result) {
            adressInBlockchain(result);
        });
    }
});

/**
 * Checks if the entered wallet address actually exists in the network. 
 * @param {*} address The address of the BlockMail node to connect to.
 */
function adressInBlockchain(address) {
    var socket = new WebSocket("ws://" + address);
    socket.onopen = function () {
        let key_request = {
            "action": "KEY",
            "recv_addr": $("#ecdsa-public").val(),
            "send_addr": $("#ecdsa-public").val(),
        };
        socket.send(JSON.stringify(key_request));
    }
    socket.onerror = function () {
        if ($(".alert").length > 0) {
            $(".alert").html("Unable to connect to BlockMail network. Please try again.");
        } else {
            $(".card-body").append(
                `<div class='alert alert-danger' role='alert'> 
                    Unable to connect to BlockMail network. Please try again.
                </div>`);
        }
    };
    socket.onmessage = function (event) {
        if (event.data != "null") {
            var ecdsa_public_text = $("#ecdsa-public").val();
            var ecdsa_private_text = $("#ecdsa-private").val();
            testKeys(ecdsa_public_text, ecdsa_private_text);
        } else {
            if ($(".alert").length > 0) {
                $(".alert").html("Keys match, but address was not found in the BlockMail network. If you have just created the account, please wait a few minutes and try again. Otherwise, please create a new account.");
            } else {
                $(".card-body").append(
                    `<div class='alert alert-danger' role='alert'> 
                        Keys match, but address was not found in the BlockMail network. If you have just created the account, please wait a few minutes and try again. Otherwise, please create a new account.
                    </div>`);
            }
        }
    };
}

/**
 * Evaluate inputs of the form and outline in red if incorrect, and display alert at bottom of form. 
 * @param {*} ecdsa_text The textual form of the ECDSA public/private key.
 * @param {*} is_public A boolean value.
 */
function checkECDSAKey(ecdsa_text, is_public) {
    //Set up ID targets.
    id = "#ecdsa-public"; //If Public.
    id_label = "#ecdsa-public-file-label"
    if (!is_public) {
        id = "#ecdsa-private"; //If Private.
        id_label = "#ecdsa-private-file-label"
    }
    if (ecdsa_text == "") {
        $(id).css("border", "2px solid red !important");
        $(id_label).css("border", "2px solid red !important");
        if ($(".alert").length > 0) {
            $(".alert").html("You must enter or upload an ECDSA " + (is_public ? "Public" : "Private") + " Key to authenticate with. ");
        } else {
            $(".card-body").append(
                `<div class='alert alert-danger' role='alert'>
                    You must enter or upload an ECDSA ` + (is_public ? "Public" : "Private") + ` Key to authenticate with.
                </div>`);
        }
        return false;
    }
    return true
}

/**
 * Compare the keys after checking that the public key is not on the network.
 * @param {*} public The ECDSA public key.
 * @param {*} private The ECDSA private key
 */
function testKeys(public, private) {
    compare_public = EC_INSTANCE.keyFromPrivate(private, "hex").getPublic().encode("hex");
    if (compare_public == public) {
        var date = new Date();
        date.setTime(date.getTime() + 3600000); //An hour from now.
        document.cookie = "ecdsa_public=" + public + ";expires=" + date.toUTCString() + "; path=/";
        document.cookie = "ecdsa_private=" + private + ";expires=" + date.toUTCString() + "; path=/";
        $(".card-body").append(
            `<div class='alert alert-success' role='alert'> 
                Authentication Successful! You will be redirected momentarily... 
            </div>`);
        $("#auth-btn").attr("disabled", true);
        setTimeout(function () {
            window.location = "mail.html";
        }, 2000);
        return true;
    }
    if ($(".alert").length > 0) {
        $(".alert").html("Authentication failed. Please try again.");
    } else {
        $(".card-body").append(
            `<div class='alert alert-danger' role='alert'> 
                Authentication failed. Please try again. 
            </div>`);
    }
    return false;
}

/** 
 * Wait for file upload. If file uploaded, place into text area, and grey out upload button. 
 */
$("#ecdsa-public-file").change(function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        $("#ecdsa-public").val(event.target.result);
    }
    reader.onerror = error => reject(error);
    reader.readAsText(this.files[0]);
    $("#ecdsa-public-file-label").addClass("hidden");
    $("#clear-public").removeClass("hidden");
});

/** 
 * Same as above but for private key file.
 */
$("#ecdsa-private-file").change(function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        $("#ecdsa-private").val(event.target.result);
    }
    reader.onerror = error => reject(error);
    reader.readAsText(this.files[0]);
    $("#ecdsa-private-file-label").addClass("hidden");
    $("#clear-private").removeClass("hidden");
});

/**
 * Clears the public/private key text inputs.
 * @param {*} is_public A boolean value.
 */
function clearFile(is_public) {
    $(is_public ? "#clear-public" : "#clear-private").addClass("hidden");
    $(is_public ? "#ecdsa-public" : "#ecdsa-private").val("");
    $(is_public ? "#ecdsa-public-file" : "#ecdsa-private-file").val("");
    $(is_public ? "#clear-public-label" : "#clear-private-label").addClass("hidden");
    $(is_public ? "#ecdsa-public-file-label" : "#ecdsa-private-file-label").removeClass("hidden");
}