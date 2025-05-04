import { scheduleStaticTokenRefresh ,   postrequest  } from "./utils.js";




document.addEventListener('DOMContentLoaded' , function() {
    scheduleStaticTokenRefresh();

    //part handles login form submission

    if (window.location.pathname === "/auth/login/") {
        const loginform = document.getElementById("login-form");
        if (loginform) {
            console.log("Login form found");
            loginform.addEventListener("submit", async function (event) {
                event.preventDefault();
                const data = {
                    username: document.getElementById("username").value,
                    password: document.getElementById("password").value,
                };
                const res = await postrequest("/auth/token/" , "POST" , data);
                if (res.status === 200 || res.status === 201) {
                    console.log("Login successful");
                    alert('Login successful');
                    window.location.href = "/dashboard/";
                } else {
                    alert('Login failed');
                    console.log("Login failed");
                }
            });
        }
    }

    //part handles registration form submission

    if (window.location.pathname ==="/auth/register/") {
        const registerform = document.getElementById("register-form");
        if (registerform) {
            console.log("Register form found");
            registerform.addEventListener("submit", async function (event) {
                event.preventDefault();
                const data = {
                    username: document.getElementById("username").value,
                    password: document.getElementById("password").value,
                    email: document.getElementById("email").value,
                    first_name: document.getElementById("first-name").value,
                    last_name: document.getElementById("last-name").value
                };
                const res = await postrequest("/auth/register/" , "POST" , data);
                if (res.status === 200 || res.status === 201) {
                    console.log("Registration successful");
                    alert('Registration successful');
                    window.location.href = "/auth/login/";
                } else {
                    alert('Registration failed');
                    console.log("Registration failed");
                }
            });
        }
    }

    //part handles guest registration form submission

    if (window.location.pathname === "/dashboard/create-guest/") {
        const form = document.getElementById("guest-form");
        if (form) {
            console.log("Guest form found");
            form.addEventListener("submit", async function (event) {
                event.preventDefault();
                const data = {
                    username: document.getElementById("username").value,
                    password: document.getElementById("password").value,
                    email: document.getElementById("email").value,
                    first_name: document.getElementById("first-name").value,
                    last_name: document.getElementById("last-name").value
                };
                 const res = await postrequest("/dashboard/create-guest/" , "POST" , data);
                 if (res.status === 201 || res.status === 200) {
                    console.log("Guest registration successful");
                    alert('Guest registration successful');
                    window.location.href = "/dashboard/";
                }
                else {
                    alert('Guest registration fail');
                    console.log("Guest registration failed");
                }
            });
        }
    }

})