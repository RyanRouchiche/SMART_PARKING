document.addEventListener("DOMContentLoaded", function () {
  const menu = document.querySelector("#mobile-menu");
  const menuLinks = document.querySelector(".navbar__menu");

  menu.addEventListener("click", function () {
    menu.classList.toggle("is-active");
    menuLinks.classList.toggle("active");
  });

  const swiper = new Swiper(".swiper", {
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
    loop: false,
  });

  const addButton = document.getElementById("add-slide-btn");
  const wrapper = document.getElementById("swiper-wrapper");
  const bottomSection = document.getElementById("bottom_section");

  // Create control panel for initial slide (0)
  createControlPanel(0);

  // ADD BUTTON LOGIC
  let slideCount = 1; // Number of active slides (max 10)
  let slideIdCounter = 1; // Always increasing, used for unique IDs

  addButton.addEventListener("click", () => {
    if (slideCount >= 10) {
      addButton.disabled = true;
      addButton.textContent = "Max slides reached";
      return;
    }

    const currentId = slideIdCounter++; // Use and increment ID

    const newSlide = document.createElement("div");
    newSlide.classList.add("swiper-slide");
    newSlide.setAttribute("data-slide-id", currentId);

    const content = document.createElement("div");
    content.classList.add("main__content");
    content.id = `slide-${currentId}`;

    // Clone the form container
    const originalForm = document.getElementById("formContainer");
    const clonedForm = originalForm.cloneNode(true);

    // Update the cloned form's heading
    const h1 = clonedForm.querySelector("h1");
    if (h1) h1.textContent = `Camera ${currentId}`;

    // Use a unique ID for the cloned form container if needed
    clonedForm.id = `formContainer-${currentId}`;

    // Append the cloned form into the content container
    content.appendChild(clonedForm);

    newSlide.appendChild(content);
    wrapper.appendChild(newSlide);

    createControlPanel(currentId);
    swiper.update();
    slideCount++;

    if (slideCount >= 10) {
      addButton.disabled = true;
      addButton.textContent = "Max slides reached";
      addButton.style.transform = "translateX(25%)";
    }
  });

  function deleteSlide(id) {
    const slides = document.querySelectorAll(".swiper-slide");
    slides.forEach((slide) => {
      const content = slide.querySelector(".main__content");
      if (content && content.id === `slide-${id}`) {
        slide.remove();
      }
    });

    const controls = document.querySelectorAll(".slide-control");
    controls.forEach((ctrl) => {
      if (ctrl.getAttribute("data-control-id") === id.toString()) {
        ctrl.remove();
      }
    });

    slideCount--;
    swiper.update();

    if (slideCount < 10) {
      addButton.disabled = false;
      addButton.textContent = "Add";
      addButton.style.transform = "translateX(70%)";
    }
  }

  // CONTROL PANEL GENERATOR
  function createControlPanel(id) {
    const card = document.createElement("div");
    card.classList.add("services__card", "slide-control");
    card.setAttribute("data-control-id", id);

    const icon = document.createElement("div");
    icon.style.position = "absolute";
    icon.style.top = "50%";
    icon.style.left = "100%";
    icon.style.transform = "translate(-50%, -50%)";

    const img = document.createElement("img");
    img.src = window.CAM_IMAGE_URL;
    img.style.width = "80px";
    img.style.cursor = "pointer";

    // 👇 Make cam.png clickable to switch slides
    img.addEventListener("click", () => {
      const allSlides = document.querySelectorAll(".swiper-slide");
      allSlides.forEach((slide, index) => {
        const content = slide.querySelector(".main__content");
        if (content && content.id === `slide-${id}`) {
          swiper.slideTo(index);
        }
      });
    });

    icon.appendChild(img);
    card.appendChild(icon);

    card.style.position = "relative";
    card.style.padding = "50px";
    card.style.margin = "1rem";

    const title = document.createElement("h2");
    title.textContent = `Cam ${id}`;
    title.style.color = "#fff";
    title.style.position = "absolute";
    title.style.top = "80%";
    title.style.left = "65%";
    title.style.whiteSpace = "nowrap";

    card.appendChild(title);

    const buttonContainer = document.createElement("div");
    buttonContainer.classList.add("card-buttons");
    buttonContainer.style.position = "absolute";
    buttonContainer.style.width = "100%";
    buttonContainer.style.height = "100%";
    buttonContainer.style.top = "0";
    buttonContainer.style.left = "0";
    buttonContainer.style.display = "flex";
    buttonContainer.style.flexDirection = "column";
    buttonContainer.style.justifyContent = "space-between";
    buttonContainer.style.alignItems = "flex-end";
    buttonContainer.style.padding = "10px";
    buttonContainer.style.pointerEvents = "none";

    if (id !== 0) {
      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "✕";
      deleteBtn.style.position = "absolute";
      deleteBtn.style.top = "10%";
      deleteBtn.style.right = "-35%";
      deleteBtn.style.border = "none";
      deleteBtn.style.background = "rgba(255, 0, 0, 0.7)";
      deleteBtn.style.color = "#fff";
      deleteBtn.style.borderRadius = "50%";
      deleteBtn.style.width = "-30%";
      deleteBtn.style.height = "-15%";
      deleteBtn.style.cursor = "pointer";
      deleteBtn.style.pointerEvents = "auto";

      deleteBtn.addEventListener("click", () => {
        showConfirmModal(id);
      });

      buttonContainer.appendChild(deleteBtn);
    }

    card.appendChild(buttonContainer);
    bottomSection.appendChild(card);
  }

  let pendingDeleteId = null;

  function showConfirmModal(id) {
    pendingDeleteId = id;
    document.getElementById("confirmModal").style.display = "flex";
  }

  function hideConfirmModal() {
    pendingDeleteId = null;
    document.getElementById("confirmModal").style.display = "none";
  }

  document.getElementById("confirmDeleteBtn").addEventListener("click", () => {
    if (pendingDeleteId !== null) {
      deleteSlide(pendingDeleteId);
      hideConfirmModal();
    }
  });

  document
    .getElementById("cancelDeleteBtn")
    .addEventListener("click", hideConfirmModal);
});
