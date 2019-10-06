//Wait for file upload. If file uploaded, place into text area, and grey out upload button.
document.getElementById("ecdsa-public-file").onchange = function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        document.getElementById("ecdsa-public").value = event.target.result;
    }
    reader.onerror = error => reject(error);
    reader.readAsText(document.getElementById("ecdsa-public-file").files[0]);

    document.getElementById("ecdsa-public-file-label").setAttribute("style", "display: none;");
    document.getElementById("clear-public-label").setAttribute("style", "display: block;");

};

//Same as above but for Private Key.
document.getElementById("ecdsa-private-file").onchange = function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        document.getElementById("ecdsa-private").value = event.target.result;
    }
    reader.onerror = error => reject(error);
    reader.readAsText(document.getElementById("ecdsa-private-file").files[0]);

    document.getElementById("ecdsa-private-file-label").setAttribute("style", "display: none;");
    document.getElementById("clear-private-label").setAttribute("style", "display: block;");
};

function clearFile(is_public) {
    document.getElementById(is_public ? "ecdsa-public" : "ecdsa-private").value = "";
    document.getElementById(is_public ? "ecdsa-public-file" : "ecdsa-private-file").value = "";
    document.getElementById(is_public ? "clear-public-label" : "clear-private-label").setAttribute("style", "display: none;");
    document.getElementById(is_public ? "ecdsa-public-file-label" : "ecdsa-private-file-label").setAttribute("style", "display: block;");
}