let websocket;
import { sendrequest, initwebsocketconn } from "./utils.js";

async function deleteUser(userId) {
  if (confirm("Are you sure you want to delete this user?")) {
    try {
      const response = await sendrequest(
        `/dashboard/users/${userId}/delete/`,
        "DELETE"
      );

      if (response.data) {
        alert("User deleted successfully.");
        window.location.href = "/dashboard/";
      } else {
        alert(`Error: delete user`);
      }
    } catch (error) {
      console.error("Error deleting user:", error);
      alert("An error occurred. Please try again.");
    }
  }
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
  const dvabtn = document.getElementById("DVA");
  if (dvabtn) {
    console.log("DVA button found");
    dvabtn.addEventListener("click", function () {
      window.location.href = "/parking/video/";
    });
  }

  //redirect the admin to conigure parking spot

  const markupspotButton = document.getElementById("markSpot");
  if (markupspotButton) {
    console.log("button markup spot found");
    markupspotButton.addEventListener("click", function () {
      window.location.href = "/parking/pickupSpot/";
    });
  }

  //logout button
  const logoutbutton = document.getElementById("logout-btn");
  if (logoutbutton) {
    console.log("Logout button found!");
    logoutbutton.addEventListener("click", async () => {
      const data = await sendrequest("/auth/logout/", "POST");
      if (data.data.success) {
        alert(data.data.message);
        window.location.href = "/auth/login/";
      } else {
        alert("Logout failed: " + data.data.error);
      }
    });
  }

  const cameraButton = document.getElementById("cameraconfig");
  if (cameraButton) {
    console.log("Camera button found!");
    cameraButton.addEventListener("click", function () {
      window.location.href = "/camera/config/";
    });
  }
  const cameraListButton = document.getElementById("Forms");
  if (cameraListButton) {
    console.log("Camera list button found!");
    cameraListButton.addEventListener("click", function () {
      window.location.href = "/dashboard/Forms/";
    });
  }

  if (window.location.pathname === "/dashboard/Forms/") {
    const data = await sendrequest("/dashboard/users/users-list/", "POST");
    populateUserTable(data.data.users);
    document.querySelectorAll(".delete-user-btn").forEach((button) => {
      button.addEventListener("click", async (e) => {
        const userId = e.target.getAttribute("data-user-id");
        deleteUser(userId);
      });
    });
  }
});

window.addEventListener("beforeunload", async () => {
  if (websocket && websocket.readyState === WebSocket.OPEN) {
    websocket.close();
  }
});
