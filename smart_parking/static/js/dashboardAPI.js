document.addEventListener("DOMContentLoaded", function () {
    // Send a POST request to fetch user data automatically when the page loads
    fetch("/dashboard/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Display the user data on the page
            document.getElementById("username").innerText = data.user.username;
            document.getElementById("email").innerText = data.user.email;
            document.getElementById("role").innerText = data.user.role;
            document.getElementById("user-id").innerText = data.user.id;
        } else {
            alert("You are not authenticated. Please log in.");
            window.location.href = "/login/";
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error);
        alert("An error occurred. Please try again later.");
    });

    // Logout functionality
    document.getElementById("logout-btn").addEventListener("click", function () {
        fetch("/api/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message); 
                window.location.href = "/login/"; 
            } else {
                alert("Logout failed: " + data.error); 
            }
        })
        .catch(error => {
            console.error("Error logging out:", error);
            alert("An error occurred while logging out. Please try again.");
        });
    });

    // Function to get the CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            let cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
