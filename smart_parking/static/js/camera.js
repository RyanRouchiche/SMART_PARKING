console.log("JS chargé");
import { sendrequest, postrequest, redirect } from "./utils.js";

function sendCamData() {
  const forms = document.getElementsByClassName("camera-form");
  const data = [];

  for (let form of forms) {
    const area = form.querySelector('input[name="area"]').value.trim();
    const ref = form.querySelector('input[name="ref"]').value.trim();
    const path = form.querySelector('input[name="path"]').value.trim();

    if (!area || !ref || !path) {
      showConfirmModal("Please fill in all fields for each camera.");
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
    console.log("calling the fetch request...");
    const res = await sendrequest("/camera/list-cameras/", "POST");
    if (res?.data?.success && Array.isArray(res.data.cameras)) {
      console.log("Cameras loaded successfully.");
      const cams = res.data.cameras;
      console.log(cams);
      loadcameras(cams);
    } else {
      alert("Error loading cameras.");
    }
  }
});

async function deleteCamera(cameraId) {
  if (!confirm("Are you sure you want to delete this camera?")) {
    return;
  }
  const response = await sendrequest(`/camera/delete/${cameraId}/`, "DELETE");
  if (response.data) {
    alert("Camera deleted successfully!");
    await redirect("/dashboard/");
  } else {
    alert("Error deleting camera.");
  }
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
  if (data) {
    const response = await postrequest("/camera/config/", "POST", data);
    if (response && response.ok) {
      showConfirmModal("Cameras added successfully!");
    } else {
      showConfirmModal("Error submitting cameras.");
    }
  }
}

window.sendCamData = sendCamData;
window.SendData = SendData;
