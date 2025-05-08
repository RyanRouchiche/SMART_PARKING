const errorLogin = document.getElementById("error-message-login");
const errorRegister = document.getElementById("error-message-register");

function showForm(formId) {
  document
    .querySelectorAll(".form-box")
    .forEach((form) => form.classList.remove("active"));
  document.getElementById(formId).classList.add("active");
}
function hideError() {
  errorLogin.style.display = "none";
  errorRegister.style.display = "none";
}
