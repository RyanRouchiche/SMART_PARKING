let pendingDeleteId = null;
let modalMode = null;
let swiper;
let currentLanguage;
document.addEventListener("DOMContentLoaded", function () {
  swiper = new Swiper(".swiper", {
    navigation: {
      nextEl: ".swiper-button-next",
      prevEl: ".swiper-button-prev",
    },
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
    loop: false,
    autoHeight: true,
  });

  const addButton = document.getElementById("add-slide-btn");
  const wrapper = document.getElementById("swiper-wrapper");
  const bottomSection = document.getElementById("bottom_section");

  createControlPanel(0);

  let slideCount = 1;
  let usedIds = new Set([0]);
  let releasedIds = [];

  addButton.addEventListener("click", () => {
    let currentId;
    if (releasedIds.length > 0) {
      releasedIds.sort((a, b) => a - b);
      currentId = releasedIds.shift();
    } else {
      for (let i = 0; i < 10; i++) {
        if (!usedIds.has(i)) {
          currentId = i;
          break;
        }
      }
    }

    usedIds.add(currentId);

    const newSlide = document.createElement("div");
    newSlide.classList.add("swiper-slide");
    newSlide.setAttribute("data-slide-id", currentId);

    const content = document.createElement("div");
    content.classList.add("main__content");
    content.id = `slide-${currentId}`;

    const originalForm = document.getElementById("formContainer");
    const clonedForm = originalForm.cloneNode(true);
    const inputs = clonedForm.querySelectorAll("input");
    inputs.forEach((input) => {
      input.value = "";
    });
    const h1 = clonedForm.querySelector("h1");
    currentLanguage = getCurrentLanguage();
    if (h1) {
      h1.textContent =
        currentLanguage === "en"
          ? `Camera N_${currentId} Configuration`
          : `Configuration de la caméra N_${currentId}`;
    }

    clonedForm.id = `formContainer-${currentId}`;

    content.appendChild(clonedForm);
    newSlide.appendChild(content);
    wrapper.appendChild(newSlide);

    createControlPanel(currentId);
    swiper.update();
    slideCount++;

    if (slideCount >= 10) {
      addButton.disabled = true;
      addButton.textContent = "Max slides reached";
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

    releasedIds.push(parseInt(id));
    usedIds.delete(parseInt(id));

    slideCount--;
    swiper.update();

    if (slideCount < 10) {
      addButton.disabled = false;
      addButton.textContent = "Add";
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
    icon.style.left = "0%";
    icon.style.transform = "translate(0%, -50%)";

    const img = document.createElement("img");
    img.src = window.CAM_IMAGE_URL;
    img.style.width = "80px";
    img.style.cursor = "pointer";

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
    title.style.left = "20%";
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
      deleteBtn.style.right = "10%";
      deleteBtn.style.border = "none";
      deleteBtn.style.background = "rgba(255, 0, 0, 0.7)";
      deleteBtn.style.color = "#fff";
      deleteBtn.style.borderRadius = "50%";
      deleteBtn.style.width = "-30%";
      deleteBtn.style.height = "-15%";
      deleteBtn.style.cursor = "pointer";
      deleteBtn.style.pointerEvents = "auto";

      deleteBtn.addEventListener("click", () => {
        showModal(id);
      });

      buttonContainer.appendChild(deleteBtn);
    }

    card.appendChild(buttonContainer);
    bottomSection.appendChild(card);
  }

  document.getElementById("confirmBtn").addEventListener("click", async () => {
    if (modalMode === "delete" && pendingDeleteId !== null) {
      deleteSlide(pendingDeleteId);
    }

    if (modalMode === "validate") {
      const data = sendCamData();
      SendData(data);
    }
    hideModal();
  });

  document.getElementById("cancelBtn").addEventListener("click", hideModal);
});

function resetCameraForms() {
  currentLanguage = getCurrentLanguage();
  const slides = document.querySelectorAll(".swiper-slide");
  slides.forEach((slide) => {
    const content = slide.querySelector(".main__content");
    if (content && content.id !== "slide-0") {
      slide.remove();
    }
  });

  const initialInputs = document.querySelectorAll("#slide-0 input");
  initialInputs.forEach((input) => {
    input.value = "";
  });

  const controls = document.querySelectorAll(".slide-control");
  controls.forEach((ctrl) => {
    if (ctrl.getAttribute("data-control-id") !== "0") {
      ctrl.remove();
    }
  });

  usedIds = new Set([0]);
  releasedIds = [];
  slideCount = 1;

  const addButton = document.getElementById("add-slide-btn");
  if (addButton) {
    addButton.disabled = false;

    addButton.textContent = currentLanguage === "en" ? "Add" : "Ajouter";
  }

  if (typeof swiper !== "undefined") {
    swiper.update();
    swiper.slideTo(0);
  }
}

function showModal(id = null, mode = "delete") {
  currentLanguage = getCurrentLanguage();
  pendingDeleteId = id;
  modalMode = mode;
  document.getElementById("Modal").style.display = "flex";
  const message = document.getElementById("modalMessage");
  if (message) {
    if (currentLanguage == "en") {
      message.textContent =
        mode === "delete"
          ? "Are you sure you want to delete this slide?"
          : "Do you want to validate and submit all cameras?";
    } else {
      message.textContent =
        mode === "delete"
          ? "Êtes-vous sûr de vouloir supprimer cette diapositive ?"
          : "Voulez-vous valider et soumettre toutes les caméras ?";
    }
  }
}

function hideModal() {
  pendingDeleteId = null;
  document.getElementById("Modal").style.display = "none";
}
