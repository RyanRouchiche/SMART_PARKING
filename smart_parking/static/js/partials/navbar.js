document.addEventListener("DOMContentLoaded", function () {
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
