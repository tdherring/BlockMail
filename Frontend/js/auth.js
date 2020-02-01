const EC = require("elliptic").ec;
const EC_INSTANCE = new EC("secp256k1");

//Handle initial "Authenticate" button press.
$("#auth-btn").click(function () {
    //Get values of login form fields into variables.
    var ecdsa_public_text = $("#ecdsa-public").val();
    var ecdsa_private_text = $("#ecdsa-private").val();

    if (checkECDSAKey(ecdsa_public_text, true) && checkECDSAKey(ecdsa_private_text, false)) {
        testKeys(ecdsa_public_text, ecdsa_private_text);
    }
});

//Evaluate inputs of the form and outline in red if incorrect, and display alert at bottom of form.
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
        if (!$(".alert").length > 0) {
            $(".card-body").append(
                `<div class='alert alert-danger' role='alert'> 
          You must enter or upload an ECDSA ` + (is_public ? "Public" : "Private") + ` Key to authenticate with. 
        </div>`);
        }
        return false;
    }
    return true
}

function testKeys(public, private) {
    compare_public = EC_INSTANCE.keyFromPrivate(private, "hex").getPublic().encode("hex");
    if (compare_public == public) {
        console.log("Authentication Successful!");
        var date = new Date();
        date.setTime(date.getTime() + 3600000); //An hour from now.
        document.cookie = "ecdsa_public=" + public + ";expires=" + date.toUTCString() + "; path=/";
        document.cookie = "ecdsa_private=" + private + ";expires=" + date.toUTCString() + "; path=/";
        $(".card-body").append(
            `<div class='alert alert-success' role='alert'> 
        Authentication Successful! You will be redirected momentarily... 
      </div>`);
        $("#auth-btn").attr("disabled", true);
        return true;
    }
    console.log("Authentication Failed!");
    if (!$(".alert").length > 0) {
        $(".card-body").append(
            `<div class='alert alert-danger' role='alert'> 
        Authentication failed. Please try again. 
      </div>`);
    }
    return false;
}