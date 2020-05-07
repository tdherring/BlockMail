if (getCookie("ecdsa_public") == "") {
    $("#mail-link").attr("href", "login.html");
} else {
    $("#create-acc-link, #login-link").css('display', 'none')
    $(".navbar-nav").append("<hr><a class='nav-item nav-link' id='logout-link' href='#'>Logout</a>")
}

/**
 * Wait for click of logout button. Once received, purge appropriate cookies and redirect to homepage.
 */
$("#logout-link").click(function logout() {
    document.cookie = "ecdsa_public= ;expires=Thu, 01-Jan-70 00:00:01 GMT" + "; path = /";
    document.cookie = "ecdsa_private= ;expires=Thu, 01-Jan-70 00:00:01 GMT" + "; path = /";

    window.location = "index.html";
});