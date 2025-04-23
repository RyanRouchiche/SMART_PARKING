import { getCookie } from "./utils.js";


export async function loginUser(event) {
    event.preventDefault(); // Prevent the default form submission behavior

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/api/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"), // Include CSRF token if required
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();

        if (response.ok) {
            alert("Login successful!");
            window.location.href = "/dashboard/"; // Redirect to the dashboard
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error("Login error:", error);
        alert("An error occurred during login.");
    }
}

// Attach the function to the global window object
window.loginUser = loginUser;

export async function registerUser(event) {
    event.preventDefault();
    const data = {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
        email: document.getElementById("email").value,
        first_name: document.getElementById("first-name").value,
        last_name: document.getElementById("last-name").value,
    };

    try {
        const response = await fetch("/api/register/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify(data),
        });

        const res = await response.json();
        if (response.ok) {
            alert(res.message);
        } else {
            alert(`Error: ${JSON.stringify(res)}`);
        }
    } catch (error) {
        console.error("Register error:", error);
        alert("An error occurred.");
    }
}

export async function registerGuest(event) {
    event.preventDefault();
    const data = {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
        email: document.getElementById("email").value,
        first_name: document.getElementById("first-name").value,
        last_name: document.getElementById("last-name").value,
    };

    try {
        const response = await fetch("/dashboard/create-guest/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify(data),
        });

        const res = await response.json();
        if (response.ok) {
            alert(res.message);
        } else {
            alert(`Error: ${JSON.stringify(res)}`);
        }
    } catch (error) {
        console.error("Register guest error:", error);
        alert("An error occurred.");
    }
}
