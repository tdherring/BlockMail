//Handle initial "Authenticate" button press.
function authenticate() {
    //Get values of login form fields into variables.
    var ecdsa_public_text = document.getElementById("ecdsa_public").value;
    var ecdsa_private_text = document.getElementById("ecdsa_private").value;
    var ecdsa_public_file = document.getElementById('ecdsa_public_file').files[0];
    var ecdsa_private_file = document.getElementById('ecdsa_private_file').files[0];

    checkECDSAKey(ecdsa_public_text, ecdsa_public_file, true);
    checkECDSAKey(ecdsa_private_text, ecdsa_private_file, false);
}

//Evaluate inputs of the form and outline in red if incorrect, and display alert at bottom of form.
function checkECDSAKey(ecdsa_text, ecdsa_file, is_public) {
    if (ecdsa_text == "" && ecdsa_file == undefined) {
        document.getElementById(is_public ? "ecdsa_public" : "ecdsa_private").setAttribute("style", "border: 2px solid red !important");
        document.getElementById(is_public ? "ecdsa_public_file_label" : "ecdsa_private_file_label").setAttribute("style", "border: 2px solid red !important");
        document.getElementById("login-box-warning").innerHTML =
            "<div id='login-warning' class='alert alert-danger' role='alert'> \
                You must enter or upload an ECDSA " + (is_public ? "Public" : "Private") + " Key to authenticate with. \
            </div>";
    }
    else {
        document.getElementById(is_public ? "ecdsa_public" : "ecdsa_private").setAttribute("style", "border: 1px solid #ced4da !important");
        document.getElementById(is_public ? "ecdsa_public_file_label" : "ecdsa_private_file_label").setAttribute("style", "border: 0 !important");
        if (ecdsa_public_file != undefined) {
            return true //
        }
        else {
            return false //
        }
    }
}

function fetchECDSAKey(ecdsa_key, is_file, is_public) {
    if (is_file) {
        var reader = new FileReader();
        reader.onload = function (event) {
            return event.target.result;
        }
        reader.onerror = error => reject(error);
        reader.readAsText(ecdsa_key);

        console.log(reader.onload);
    }

}