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
  const errorLogin = document.getElementById("error-message-login");
  const errorRegister = document.getElementById("error-message-register");
  if (errorLogin) {
    console.log("Hiding error messages");
    errorLogin.style.display = "none";
  }
  if (errorRegister) {
    errorRegister.style.display = "none";
  }
}

function getCurrentLanguage() {
  let currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }
  return currentLanguage;
}
