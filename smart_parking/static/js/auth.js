import { postrequest, redirect } from "./utils.js";

document.addEventListener("DOMContentLoaded", function () {
  let currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }
  //part handles login form submission
  const loginform = document.getElementById("login-form");
  const errorMessageContainer1 = document.getElementById("error-message-login");
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

        await redirect("/dashboard/");
      } else {
        errorMessageContainer1.style.display = "block";
        errorMessageContainer1.innerHTML =
          currentLanguage == "en"
            ? "Login failed. Please check your credentials and try again."
            : "Échec de la connexion. Veuillez vérifier vos identifiants et réessayer.";
      }
    });
  }

  //part handles registration form submission

  const registerform = document.getElementById("register-form");
  const errorMessageContainer = document.getElementById(
    "error-message-register"
  );
  if (registerform) {
    console.log("Register form found");
    registerform.addEventListener("submit", async function (event) {
      event.preventDefault();
      const data = {
        username: document.getElementById("username-register").value,
        password: document.getElementById("password-register").value,
        email: document.getElementById("email").value,
        first_name: document.getElementById("first-name").value,
        last_name: document.getElementById("last-name").value,
      };
      const res = await postrequest("/auth/register/", "POST", data);
      if (res.status === 200 || res.status === 201) {
        console.log("Registration successful");
        if (currentLanguage == "en") {
          showConfirmModal("Registration successful", () => {
            showForm("login-form-id");
          });
        } else {
          showConfirmModal("Inscription réussie", () => {
            showForm("login-form-id");
          });
        }
      } else {
        errorMessageContainer.style.display = "block";
        errorMessageContainer.innerHTML =
          currentLanguage == "en"
            ? "Registration failed. Please check your credentials and try again."
            : " Échec de l'inscription. Veuillez vérifier vos informations et réessayer.";
      }
    });
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

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        const data = {
          username: document.getElementById("username").value,
          password: document.getElementById("password").value,
          email: document.getElementById("email").value,
          first_name: document.getElementById("first-name").value,
          last_name: document.getElementById("last-name").value,
        };

        try {
          const res = await postrequest(
            "/dashboard/create-guest/",
            "POST",
            data
          );

          if (res.status === 201 || res.status === 200) {
            console.log("Guest registration successful");
            if (currentLanguage == "en") {
              showConfirmModal(
                "Guest registration successful. Please confirm your email",
                () => {
                  resetGuestForm();
                }
              );
            } else {
              showConfirmModal(
                "Inscription invité réussie. Veuillez confirmer votre adresse e-mail.",
                () => {
                  resetGuestForm();
                }
              );
            }
          } else {
            errorMessageContainer.style.display = "block";
            errorMessageContainer.innerHTML =
              currentLanguage == "en"
                ? "Guest registration failed. Please check your credentials and try again."
                : "L'inscription en tant qu'invité a échoué. Veuillez vérifier vos informations et réessayer.";
          }
        } catch (err) {
          console.error("Request failed:", err);
          errorMessageContainer.style.display = "block";
          errorMessageContainer.innerHTML =
            currentLanguage == "en"
              ? "An unexpected error occurred."
              : "Une erreur inattendue est survenue.";
        } finally {
          if (submitBtn) submitBtn.disabled = false;
          rechargeUsers();
        }
      });
    }
  }
});
