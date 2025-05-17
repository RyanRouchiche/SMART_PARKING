const errorLogin = document.getElementById("error-message-login");
const errorRegister = document.getElementById("error-message-register");
const login = document.getElementById("login");
const closeFormBtns = document.querySelectorAll(".close-form-btn");

function showForm(formId) {
  document
    .querySelectorAll(".form-box")
    .forEach((form) => form.classList.remove("active"));

  const form = document.getElementById(formId);
  form.classList.add("active");

  form.querySelectorAll("input").forEach((input) => {
    input.value = "";
  });

  form.querySelectorAll(".error-message").forEach((error) => {
    error.style.display = "none";
  });
}
function showLogin() {
  document
    .querySelectorAll(".form-box")
    .forEach((form) => form.classList.remove("active"));

  const loginForm = document.getElementById("login-form-id");
  loginForm.classList.add("active");

  loginForm.querySelectorAll("input").forEach((input) => {
    input.value = "";
  });

  loginForm.querySelectorAll(".error-message").forEach((error) => {
    error.style.display = "none";
  });
}

function hideForms() {
  document
    .querySelectorAll(".form-box")
    .forEach((form) => form.classList.remove("active"));

  document.querySelectorAll("form").forEach((form) => {
    form.querySelectorAll("input").forEach((input) => {
      input.value = "";
    });
    form.querySelectorAll(".error-message").forEach((error) => {
      error.style.display = "none";
    });
  });
}

function hideError() {
  errorLogin.style.display = "none";
  errorRegister.style.display = "none";
}

closeFormBtns.forEach((button) => {
  button.style.position = "relative";
  button.style.top = "0px";
  button.style.right = "0px";
  button.style.border = "none";
  button.style.backgroundColor = "#1c1c1c";
  button.style.color = "#fff";
  button.style.borderRadius = "50%";
  button.style.width = "30px";
  button.style.height = "30px";
  button.style.cursor = "pointer";
  button.style.pointerEvents = "auto";
  button.style.fontSize = "20px";
  button.style.transform = "translateX(1200%)";
});
