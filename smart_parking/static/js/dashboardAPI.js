let websocket;
import { sendrequest, initwebsocketconn, redirect } from "./utils.js";
let currentLanguage;

async function deleteUser(userId) {
  currentLanguage = getCurrentLanguage();
  ConfirmPopup();
  const message = document.getElementById("modalMessage");
  if (message) {
    const msg =
      currentLanguage === "en"
        ? "Are you sure you want to delete this user?"
        : "Êtes-vous sûr de vouloir supprimer cet utilisateur ?";
    message.textContent = msg;
  }

  const confirmBtn = document.getElementById("confirmBtn");
  const cancelBtn = document.getElementById("cancelBtn");
  confirmBtn.onclick = async () => {
    HidePopup();
    try {
      const response = await sendrequest(
        `/dashboard/users/${userId}/delete/`,
        "DELETE"
      );
      if (response.data) {
        let userDeleted =
          currentLanguage === "en"
            ? "User deleted successfully."
            : "Utilisateur supprimé avec succès.";
        showConfirmModal(userDeleted);
        rechargeUsers();
      } else {
        let userDeleted =
          currentLanguage === "en"
            ? "Error: delete user."
            : "Erreur : suppression de l'utilisateur.";
        showConfirmModal(userDeleted);
      }
    } catch (error) {
      let userDeleted =
        currentLanguage === "en"
          ? "An error occurred. Please try again."
          : "Une erreur est survenue. Veuillez réessayer.";
      showConfirmModal(userDeleted);
    }
  };

  cancelBtn.onclick = () => {
    HidePopup();
  };
}

function updateUserStatus(event) {
  const data = JSON.parse(event.data);
  console.log("WebSocket message received:", data);
  const statusElement = document.getElementById(`status-${data.user_id}`);
  if (statusElement) {
    console.log("status");
    statusElement.innerText = data.status;
  }
}

async function loaddashboard() {
  const data = await sendrequest("/dashboard/", "POST");
  document.getElementById("username").innerText = data.data.user.username;
  document.getElementById("email").innerText = data.data.user.email;
  document.getElementById("role").innerText = data.data.user.role;
  document.getElementById("user-id").innerText = data.data.user.id;
}

function populateUserTable(users) {
  const tableBody = document.getElementById("user-table-body");
  if (!tableBody) {
    console.error("Table body element not found!");
    return;
  }

  tableBody.innerHTML = "";
  users.forEach((user) => {
    const row = document.createElement("tr");
    row.innerHTML = `
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.first_name}</td>
                <td>${user.last_name}</td>
                <td id="status-${user.id}">${user.status}</td>
                <td>
                    <button class="delete-user-btn" data-user-id="${user.id}" >Delete</button>
                </td>
            `;
    tableBody.appendChild(row);
  });
}

document.addEventListener("DOMContentLoaded", async function () {
  //init websocket  connection
  //which protocole using
  const wsschema = window.location.protocol === "https:" ? "wss" : "ws";
  websocket = initwebsocketconn(wsschema, "ws/user-status/");
  console.log("WebSocket URL:", websocket.url);

  websocket.onopen = function () {
    console.log("WebSocket connection established.");
  };

  websocket.onmessage = function (event) {
    updateUserStatus(event);
  };

  if (window.location.pathname === "/dashboard/") {
    loaddashboard();
    document.querySelectorAll(".services__card").forEach((card) => {
      const imageUrl = card.getAttribute("data-bg");
      card.style.backgroundImage = `linear-gradient(
        to bottom,
        rgba(0, 0, 0, 0) 0%,
        rgba(17, 17, 17, 0.6) 100%
      ), url('${imageUrl}')`;
    });
  }
  const parkingbtn = document.getElementById("navbar__logo");
  if (parkingbtn) {
    parkingbtn.addEventListener("click", async (e) => {
      e.preventDefault();
      await redirect("/dashboard/");
    });
  }

  const dvabtn = document.getElementById("DVA");
  const simulationCard = document.getElementById("simulationCard");
  if (dvabtn) {
    console.log("DVA button found");
    dvabtn.addEventListener("click", async function () {
      await redirect("/parking/video/");
    });
  }
  if (simulationCard) {
    simulationCard.addEventListener("click", async function () {
      await redirect("/parking/video/");
    });
  }

  const LCDbtn = document.getElementById("LCD");
  const lcdCard = document.getElementById("lcdCard");
  if (LCDbtn) {
    console.log("LCDbtn button found");
    LCDbtn.addEventListener("click", async function () {
      await redirect("/dashboard/lcd/");
    });
  }
  if (lcdCard) {
    lcdCard.addEventListener("click", async function () {
      await redirect("/dashboard/lcd/");
    });
  }

  //redirect the admin to conigure parking spot

  const markupspotButton = document.getElementById("markSpot");
  const PickupCard = document.getElementById("PickupCard");

  if (markupspotButton) {
    console.log("button markup spot found");
    markupspotButton.addEventListener("click", async function () {
      await redirect("/parking/pickupSpot/");
    });
  }
  if (PickupCard) {
    PickupCard.addEventListener("click", async function () {
      await redirect("/parking/pickupSpot/");
    });
  }

  //logout button
  const logoutbutton = document.getElementById("logout-btn");
  if (logoutbutton) {
    currentLanguage = getCurrentLanguage();
    console.log("Logout button found!");
    logoutbutton.addEventListener("click", async () => {
      const data = await sendrequest("/auth/logout/", "POST");
      if (data.data.success) {
        const msg =
          currentLanguage === "en"
            ? "logout succesfull"
            : "Déconnexion aves succees";
        showConfirmModal(msg, () => {
          window.location.href = "/";
        });
      } else {
        const msg =
          currentLanguage === "en" ? "logout failed" : "Déconnexion échouée";
        showConfirmModal(msg);
      }
    });
  }

  const cameraButton = document.getElementById("cameraconfig");
  const SetupCard = document.getElementById("SetupCard");
  if (cameraButton) {
    console.log("Camera button found!");
    cameraButton.addEventListener("click", async function () {
      await redirect("/camera/config/");
    });
  }
  if (SetupCard) {
    SetupCard.addEventListener("click", async function () {
      await redirect("/camera/config/");
    });
  }

  const cameraListButton = document.getElementById("Forms");
  const FormsCard = document.getElementById("FormsCard");

  if (cameraListButton) {
    console.log("Camera list button found!");
    cameraListButton.addEventListener("click", async function () {
      await redirect("/dashboard/Forms/");
    });
  }
  if (FormsCard) {
    FormsCard.addEventListener("click", async function () {
      await redirect("/dashboard/Forms/");
    });
  }

  if (window.location.pathname === "/dashboard/Forms/") {
    rechargeUsers();
  }
});

window.addEventListener("beforeunload", async () => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.close();
  }
});

async function rechargeUsers() {
  const data = await sendrequest("/dashboard/users/users-list/", "POST");
  populateUserTable(data.data.users);
  document.querySelectorAll(".delete-user-btn").forEach((button) => {
    button.addEventListener("click", async (e) => {
      const userId = e.target.getAttribute("data-user-id");
      deleteUser(userId);
    });
  });
}
window.rechargeUsers = rechargeUsers;
