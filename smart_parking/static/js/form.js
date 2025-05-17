const errorLogin = document.getElementById("error-message-login");
const errorRegister = document.getElementById("error-message-register");

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

function hideError() {
  errorLogin.style.display = "none";
  errorRegister.style.display = "none";
}
