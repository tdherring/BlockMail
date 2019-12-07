//Wait for file upload. If file uploaded, place into text area, and grey out upload button.
$("#ecdsa-public-file").change(function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        $("#ecdsa-public").val(event.target.result);
    }
    reader.onerror = error => reject(error);
    reader.readAsText(document.getElementById("ecdsa-public-file").files[0]);

$("#ecdsa-private-file").change(function () {
    var reader = new FileReader();
    reader.onload = function (event) {
        $("#ecdsa-private").val(event.target.result);
    }
    reader.onerror = error => reject(error);
    reader.readAsText(this.files[0]);
    $("#ecdsa-private-file-label").css("display", "none");
    $("#clear-private-label").css("display", "block");
});

function clearFile(is_public) {
    $(is_public ? "#ecdsa-public" : "#ecdsa-private").val("");
    $(is_public ? "#ecdsa-public-file" : "#ecdsa-private-file").val("");
    $(is_public ? "#clear-public-label" : "#clear-private-label").css("display", "none");
    $(is_public ? "#ecdsa-public-file-label" : "#ecdsa-private-file-label").css("display", "block");
}