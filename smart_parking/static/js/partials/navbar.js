document.addEventListener("DOMContentLoaded", function () {
  const langSelect = document.getElementById("lang-select");
  const langForm = document.getElementById("lang-form");
  const langInput = document.getElementById("lang-input");
  const csrfTokenInput = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  );

  let currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }

  if (langSelect) {
    langSelect.value = currentLanguage;
  }

  if (langSelect && langForm && langInput && csrfTokenInput) {
    langSelect.addEventListener("change", async function () {
      const selectedLanguage = langSelect.value;
      localStorage.setItem("language", selectedLanguage);
      langInput.value = selectedLanguage;

      const formData = new URLSearchParams();
      formData.append("language", langInput.value);
      formData.append(
        "next",
        langForm.querySelector('input[name="next"]').value
      );

      try {
        const response = await fetch(langForm.action, {
          method: "POST",
          headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": csrfTokenInput.value,
          },
          body: formData.toString(),
        });

        if (response.ok) {
          window.location.reload();
        } else {
          const msg =
            currentLanguage === "en"
              ? "Language change failed"
              : "Le changement de langue a échoué";
          showConfirmModal(msg);
        }
      } catch (error) {
        const msg =
          currentLanguage === "en"
            ? "An error occurred while changing language"
            : "Une erreur s'est produite lors du changement de langue.";
        showConfirmModal(msg);
      }
    });
  }
  if (window.location.pathname !== "/") {
    // Handle menu toggle for mobile view
    const menu = document.querySelector("#mobile-menu");
    const menuLinks = document.querySelector(".navbar__menu");

    if (menu && menuLinks) {
      menu.addEventListener("click", function () {
        menu.classList.toggle("is-active");
        menuLinks.classList.toggle("active");
      });
    }

    // Highlight active button based on the current URL
    const path = window.location.pathname;
    const pathToButtonId = {
      "/parking/video/": "DVA",
      "/parking/pickupSpot/": "markSpot",
      "/camera/config/": "cameraconfig",
      "/dashboard/Forms/": "Forms",
      "/dashboard/lcd/": "LCD",
    };

    const activeButtonId = pathToButtonId[path];
    if (activeButtonId) {
      const activeBtn = document.getElementById(activeButtonId);
      if (activeBtn) {
        activeBtn.classList.add("active");
      }
    }
  }
});

function getCurrentLanguage() {
  currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }
  return currentLanguage;
}
function getCSRFToken() {
  return document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
}
