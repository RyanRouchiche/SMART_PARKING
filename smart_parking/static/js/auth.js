import { postrequest } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  //part handles login form submission

  const loginform = document.getElementById("login-form");
  const errorMessageContainer = document.getElementById("error-message-login");
  if (loginform) {
    console.log("Login form found");
    loginform.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
      };
      const res = await postrequest("/auth/token/", "POST", data);
      if (res.status === 200 || res.status === 201) {
        console.log("Login successful");
        window.location.href = "/dashboard/";
      } else {
        errorMessageContainer.style.display = "block";
        errorMessageContainer.innerHTML =
          "Login failed. Please check your credentials and try again.";
      }
    });
  }

  //part handles registration form submission

  if (window.location.pathname === "/auth/register/") {
    const registerform = document.getElementById("register-form");
    const errorMessageContainer = document.getElementById(
      "error-message-register"
    );
    if (registerform) {
      console.log("Register form found");
      registerform.addEventListener("submit", async function (event) {
        event.preventDefault();
        const data = {
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
          email: document.getElementById("email").value,
          first_name: document.getElementById("first-name").value,
          last_name: document.getElementById("last-name").value,
        };
        const res = await postrequest("/auth/register/", "POST", data);
        if (res.status === 200 || res.status === 201) {
          console.log("Registration successful");
          alert("Registration successful");
          window.location.href = "/auth/login/";
        } else {
          errorMessageContainer.style.display = "block"; // Show the error message container
          errorMessageContainer.innerHTML =
            "Registration failed. Please check your credentials and try again.";
        }
      });
    }
  }

  //part handles guest registration form submission

  if (window.location.pathname === "/dashboard/Forms/") {
    const form = document.getElementById("guest-form");
    const errorMessageContainer = document.getElementById(
      "error-message-guest"
    );
    if (form) {
      console.log("Guest form found");
      form.addEventListener("submit", async function (event) {
        event.preventDefault();
        const data = {
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
          email: document.getElementById("email").value,
          first_name: document.getElementById("first-name").value,
          last_name: document.getElementById("last-name").value,
        };
        const res = await postrequest("/dashboard/create-guest/", "POST", data);
        if (res.status === 201 || res.status === 200) {
          console.log("Guest registration successful");
          alert("Guest registration successful . Please confirm your email");
          window.location.href = "/dashboard/";
        } else {
          errorMessageContainer.style.display = "block"; // Show the error message container
          errorMessageContainer.innerHTML =
            "Guest registration fail. Please check your credentials and try again.";
        }
      });
    }
  }
});
