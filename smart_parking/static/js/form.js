const errorLogin = document.getElementById("error-message-login");
const errorRegister = document.getElementById("error-message-register");

document.addEventListener("DOMContentLoaded", function () {
  const langSelect = document.getElementById("lang-select");
  const langForm = document.getElementById("lang-form");
  let currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }

  if (langSelect) {
    langSelect.value = currentLanguage;
  }

  if (langSelect && langForm) {
    langSelect.addEventListener("change", function () {
      const selectedLanguage = langSelect.value;
      localStorage.setItem("language", selectedLanguage);
      const langInput = document.getElementById("lang-input");
      if (langInput) {
        langInput.value = selectedLanguage;
      }
      langForm.submit();
    });
  }
});

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
  if (errorLogin) {
    errorLogin.style.display = "none";
  }
  if (errorRegister) {
    errorRegister.style.display = "none";
  }
}

function getCurrentLanguage() {
  currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }
  return currentLanguage;
}
