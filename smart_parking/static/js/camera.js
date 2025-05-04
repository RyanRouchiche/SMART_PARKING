console.log("JS chargé");
import { scheduleStaticTokenRefresh , sendrequest  , postrequest  } from "./utils.js";



function addCameraForm() {
  const formContainer = document.getElementById("formContainer");

  const formDiv = document.createElement("div");
  formDiv.className = "camera-form";

  formDiv.innerHTML = `
      <label>Zone (area):</label>
      <input type="text" name="area" placeholder="Ex: Zone B">
      <label>Référence (ref):</label>
      <input type="text" name="ref" placeholder="Ex: CAM02">
      <label>Chemin RTSP/HTTP (path):</label>
      <input type="text" name="path" placeholder="Ex: rtsp://...">
    `;

  formContainer.appendChild(formDiv);
}

function sendCamData() {
  const formContainer = document.getElementById("formContainer");
  const forms = formContainer.getElementsByClassName("camera-form");

  const data = [];

  for (let form of forms) {
    const area = form.querySelector('input[name="area"]').value.trim();
    const ref = form.querySelector('input[name="ref"]').value.trim();
    const path = form.querySelector('input[name="path"]').value.trim();

    if (!area || !ref || !path) {
      alert("Veuillez remplir tous les champs pour chaque caméra.");
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
              <td>${camera.id}</td>
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
  scheduleStaticTokenRefresh();
  e.preventDefault();
  console.log("Document loaded. Setting up event listeners.");
  

  if (window.location.pathname === "/camera/config/") {
    const addCameraButton = document.getElementById("addcam");
    if (addCameraButton) {
      console.log("Add camera button found.");
      addCameraButton.addEventListener("click", function () {
        addCameraForm();
      });
    }

    const validateButton = document.getElementById("validatecam");
    if (validateButton) {
      console.log("Validate button found.");
      validateButton.addEventListener("click", async (e) => {
        e.preventDefault();
        const data = sendCamData();
        if (data) {
          const response = await postrequest("/camera/config/", "POST", data);
          if (response && response.ok) {
            alert("Cameras added successfully!");
            window.location.href = "/dashboard/";
          }
        }
      });
    }
  }

  if (window.location.pathname === "/camera/list-cameras/") {
    console.log("calling the fetch request...");
    const res = await sendrequest("/camera/list-cameras/", "POST");
    if (res && res.cameras) {
      console.log("Cameras loaded successfully.");
      const cams = res.cameras;
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
  if (response && response.ok) {
    alert("Camera deleted successfully!");
    window.location.href = "/dashboard/";
   
  } else {
    alert("Error deleting camera.");
  }
}
