console.log("JS chargé");
import { sendrequest, postrequest, redirect } from "./utils.js";
let currentLanguage;
function sendCamData() {
  const forms = document.getElementsByClassName("camera-form");
  const data = [];
  currentLanguage = getCurrentLanguage();
  for (let form of forms) {
    const area = form.querySelector('input[name="area"]').value.trim();
    const ref = form.querySelector('input[name="ref"]').value.trim();
    const path = form.querySelector('input[name="path"]').value.trim();

    if (!area || !ref || !path) {
      const msg =
        currentLanguage === "en"
          ? "Please fill in all fields for each camera."
          : "Veuillez remplir tous les champs pour chaque caméra.";
      showConfirmModal(msg);
      return;
    }
    data.push({ area, ref, path });
  }
  return data;
}

function loadcameras(cameras) {
  const tbody = document.querySelector("#cameraTable tbody");
  tbody.innerHTML = "";

  cameras.forEach((camera) => {
    const cameraRow = document.createElement("tr");
    cameraRow.className = "camera-item";

    cameraRow.innerHTML = `
              <td style="display: none;">${camera.id}</td>
              <td>${camera.ref}</td>
              <td>${camera.area}</td>
              <td>${camera.path}</td>
              <td>${camera.is_active}</td>
              <td><button class="delete-cam-btn">delete</button></td>
          `;
    tbody.appendChild(cameraRow);
  });

  document.querySelectorAll(".delete-cam-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const cameraId = e.target.closest("tr").querySelector("td").innerText;
      await deleteCamera(cameraId);
    });
  });
}

document.addEventListener("DOMContentLoaded", async function (e) {
  e.preventDefault();
  console.log("Document loaded. Setting up event listeners.");

  if (window.location.pathname === "/camera/config/") {
    const validateButton = document.getElementById("validatecam");
    if (validateButton) {
      console.log("Validate button found.");
      validateButton.addEventListener("click", (e) => {
        e.preventDefault();
        window.showModal(null, "validate");
      });
    }
  }

  if (window.location.pathname === "/dashboard/Forms/") {
    rechargeCams();
  }
});

async function deleteCamera(cameraId) {
  ConfirmPopup();
  const message = document.getElementById("modalMessage");
  currentLanguage = getCurrentLanguage();
  if (message) {
    const msg =
      currentLanguage === "en"
        ? "Are you sure you want to delete this camera?"
        : "Êtes-vous sûr de vouloir supprimer cette caméra ?";
    message.textContent = msg;
  }

  const confirmBtn = document.getElementById("confirmBtn");
  const cancelBtn = document.getElementById("cancelBtn");

  confirmBtn.onclick = async () => {
    HidePopup();
    const response = await sendrequest(`/camera/delete/${cameraId}/`, "DELETE");
    if (response.data) {
      const successMsg =
        currentLanguage === "en"
          ? "Camera deleted successfully!"
          : "Caméra supprimée avec succès !";
      showConfirmModal(successMsg);
      rechargeCams();
    } else {
      const errorMsg =
        currentLanguage === "en"
          ? "Error deleting camera."
          : "Erreur lors de la suppression de la caméra.";
      showConfirmModal(errorMsg);
    }
  };

  cancelBtn.onclick = () => {
    HidePopup();
  };
}

function hideError() {
  const errorGuest = document.getElementById("error-message-guest");
  if (errorGuest) {
    errorGuest.style.display = "none";
  }
}
document.querySelectorAll("#guest-form input").forEach((input) => {
  input.addEventListener("focus", hideError);
});

async function SendData(data) {
  const currentLanguage = getCurrentLanguage();
  if (data) {
    const response = await postrequest("/camera/config/", "POST", data);
    const successMsg =
      currentLanguage === "en"
        ? "Cameras added successfully!"
        : "Caméras ajoutées avec succès !";
    const errorMsg =
      currentLanguage === "en"
        ? "Error submitting cameras."
        : "Erreur lors de la soumission des caméras.";

    if (response && response.ok) {
      showConfirmModal(successMsg);
      resetCameraForms();
    } else {
      showConfirmModal(errorMsg);
    }
  }
}

async function rechargeCams() {
  const currentLanguage = getCurrentLanguage();
  console.log("calling the fetch request...");
  const res = await sendrequest("/camera/list-cameras/", "POST");

  if (res?.data?.success && Array.isArray(res.data.cameras)) {
    console.log("Cameras loaded successfully.");
    const cams = res.data.cameras;
    console.log(cams);
    loadcameras(cams);
  } else {
    const errorMsg =
      currentLanguage === "en"
        ? "Error loading cameras."
        : "Erreur lors du chargement des caméras.";
    showConfirmModal(errorMsg);
  }
}

function resetGuestForm() {
  const form = document.getElementById("guest-form");
  if (form) {
    form.reset();
  }
}

window.sendCamData = sendCamData;
window.SendData = SendData;
window.rechargeCams = rechargeCams;
window.HidePopup = HidePopup;
window.resetGuestForm = resetGuestForm;
