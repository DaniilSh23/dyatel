document.getElementById("add_sample_message").addEventListener("click", function() {
    var forms = document.getElementsById("sample_message_form");
    var data = [];
    for (var i = 0; i < forms.length; i++) {
        data.push(new FormData(forms[i]));
    }
    fetch("/submit-changes", {
        method: "POST",
        body: data
    })
    .then(response => response.json())
    .then(data => {
        // handle the response from the server
    });
});