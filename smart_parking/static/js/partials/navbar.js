document.addEventListener("DOMContentLoaded", function () {
  const menu = document.querySelector("#mobile-menu");
  const menuLinks = document.querySelector(".navbar__menu");

  if (menu && menuLinks) {
    menu.addEventListener("click", function () {
      menu.classList.toggle("is-active");
      menuLinks.classList.toggle("active");
    });
  }
  const path = window.location.pathname;
  console.log("path : ", path);
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
});
