//Handle initial "Authenticate" button press.
function authenticate() {
    //Get values of login form fields into variables.
    var ecdsa_public_text = document.getElementById("ecdsa-public").value;
    var ecdsa_private_text = document.getElementById("ecdsa-private").value;

    var is_public_file = checkECDSAKey(ecdsa_public_text, true);
    var is_private_file = checkECDSAKey(ecdsa_private_text, false);
}

//Evaluate inputs of the form and outline in red if incorrect, and display alert at bottom of form.
function checkECDSAKey(ecdsa_text, ecdsa_file, is_public) {
    //Set up ID targets.
    id = "ecdsa-public"; //If Public.
    id_label = "ecdsa-public-file-label"
    if (!is_public) {
        id = "ecdsa-private"; //If Private.
        id_label = "ecdsa-private-file-label"
    }
    if (ecdsa_text == "" && ecdsa_file == undefined) {
        document.getElementById(id).setAttribute("style", "border: 2px solid red !important;");
        document.getElementById(id_label).setAttribute("style", "border: 2px solid red !important;");
        document.getElementById("login-box-warning").innerHTML =
            "<div id='login-warning' class='alert alert-danger' role='alert'> \
                You must enter or upload an ECDSA " + (is_public ? "Public" : "Private") + " Key to authenticate with. \
            </div>";
    }
    else {
        document.getElementById(id).setAttribute("style", "border: 1px solid #ced4da !important;");
        document.getElementById(id_label).setAttribute("style", "border: 0 !important;");
    }
}