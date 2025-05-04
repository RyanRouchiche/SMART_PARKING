let websocket;
import { scheduleStaticTokenRefresh , sendrequest  , initwebsocketconn  } from "./utils.js";

async function deleteUser(userId) {
  if (confirm("Are you sure you want to delete this user?")) {
    const csrftoken = document.querySelector('input[name="csrfmiddlewaretoken"]').value

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
        fetchUsers();
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
  document.getElementById("username").innerText = data.user.username;
  document.getElementById("email").innerText = data.user.email;
  document.getElementById("role").innerText = data.user.role;
  document.getElementById("user-id").innerText = data.user.id;

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
                <td>${user.id}</td>
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

  loaddashboard();

  if (window.location.pathname === "/dashboard/") {

    //redirect the admin to create guest account
    const guestcreateButton = document.getElementById("guest");
    if (guestcreateButton) {
      console.log("guest botton found");
      guestcreateButton.addEventListener("click", function () {
        window.location.href = "/dashboard/create-guest/";
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
    if(logoutbutton) {
      console.log("Logout button found!");
      logoutbutton.addEventListener('click' , async ()=> {
        const data = await sendrequest("/auth/logout/", "POST");
        if (data.success) {
          alert(data.message);
          window.location.href = "/auth/login/";
        } else {
          alert("Logout failed: " + data.error);
        }
      })
    }

    //user list button
    const userlistbutton = document.getElementById("user-list-button");
    if (userlistbutton) {
      console.log("User list button found!");
      userlistbutton.addEventListener("click", function () {
        window.location.href = "/dashboard/users/users-list/";
      });
    } else {
      console.error("User list button not found!");
    }

    const cameraButton = document.getElementById("cameraconfig");
    if (cameraButton) {
      console.log("Camera button found!");
      cameraButton.addEventListener("click", function () {
        window.location.href = "/camera/config/";
      });
    } else {
      console.error("Camera button not found!");
    }

    const cameraListButton = document.getElementById("cameralist");
    if (cameraListButton) {
      console.log("Camera list button found!");
      cameraListButton.addEventListener("click", function () {
        window.location.href = "/camera/list-cameras/";
      });
    } else {
      console.error("Camera list button not found!");
    }
  }


  if (window.location.pathname === "/dashboard/users/users-list/") {
    const data= await sendrequest("/dashboard/users/users-list/", "POST")
    populateUserTable(data.users);
    document.querySelectorAll(".delete-user-btn").forEach((button) => {
      button.addEventListener("click", async  (e) =>{
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