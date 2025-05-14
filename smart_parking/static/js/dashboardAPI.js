let websocket;
import {
  scheduleStaticTokenRefresh,
  sendrequest,
  initwebsocketconn,
} from "./utils.js";

async function deleteUser(userId) {
  if (confirm("Are you sure you want to delete this user?")) {
    const csrftoken = document.querySelector(
      'input[name="csrfmiddlewaretoken"]'
    ).value;

    try {
      const response = await fetch(`/dashboard/users/${userId}/delete/`, {
        method: "DELETE",
        credentials: "include",

        headers: {
          "X-CSRFToken": csrftoken,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ user_id: userId }),
      });

      if (response.ok) {
        alert("User deleted successfully.");
        window.location.href = "/dashboard/";
      } else {
        const data = await response.json();
        alert(`Error: ${data.error}`);
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
  const menu = document.querySelector("#mobile-menu");
  const menuLinks = document.querySelector(".navbar__menu");

  menu.addEventListener("click", function () {
    menu.classList.toggle("is-active");
    menuLinks.classList.toggle("active");
  });

  // loading images to services

  scheduleStaticTokenRefresh();

  //init websocket  connection
  //which protocole using
  const wsschema = window.location.protocol === "https:" ? "wss" : "ws";
  websocket = initwebsocketconn(wsschema);
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
  } else {
    console.error("DVA button not found!");
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

  //user list button
  // const userlistbutton = document.getElementById("user-list-button");
  // if (userlistbutton) {
  //   console.log("User list button found!");
  //   userlistbutton.addEventListener("click", function () {
  //     window.location.href = "/dashboard/users/users-list/";
  //   });
  // } else {
  //   console.error("User list button not found!");
  // }

  const cameraButton = document.getElementById("cameraconfig");
  if (cameraButton) {
    console.log("Camera button found!");
    cameraButton.addEventListener("click", function () {
      window.location.href = "/camera/config/";
    });
  } else {
    console.error("Camera button not found!");
  }

  const cameraListButton = document.getElementById("Forms");
  if (cameraListButton) {
    console.log("Camera list button found!");
    cameraListButton.addEventListener("click", function () {
      window.location.href = "/dashboard/Forms/";
    });
  } else {
    console.error("Camera list button not found!");
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
    // await sendrequest("/auth/logout/", "POST");
  }
});
