import { formPostRequest } from "./../utils.js";

document.addEventListener("DOMContentLoaded", function () {
  const langSelect = document.getElementById("lang-select");
  const langForm = document.getElementById("lang-form");
  const langInput = document.getElementById("lang-input");
  const csrfTokenInput = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  );

  let currentLanguage =
    localStorage.getItem("language") || document.documentElement.lang || "en";

  if (langSelect) {
    langSelect.value = currentLanguage;
  }

  if (langSelect && langForm && langInput && csrfTokenInput) {
    langSelect.addEventListener("change", async function () {
      const selectedLanguage = langSelect.value;
      localStorage.setItem("language", selectedLanguage);
      langInput.value = selectedLanguage;

      const payload = {
        language: selectedLanguage,
        next: langForm.querySelector('input[name="next"]').value,
      };

      const response = await formPostRequest(langForm.action, payload);

      if (response.ok) {
        window.location.reload();
      } else {
        const msg =
          getCurrentLanguage() === "en"
            ? "Language change failed"
            : "Le changement de langue a échoué";
        showConfirmModal(msg);
      }
    });
  }
});

function getCurrentLanguage() {
  return (
    localStorage.getItem("language") || document.documentElement.lang || "en"
  );
}
