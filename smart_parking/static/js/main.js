// import { fetchDashboardData, fetchUsers } from "./dashboard.js";
// import { loginUser, registerUser, registerGuest } from "./auth.js";
// import { initUserStatusWebSocket } from "./websocket.js";

// document.addEventListener("DOMContentLoaded", () => {
//     if (window.location.pathname === "/dashboard/") {
//         fetchDashboardData();
//         initUserStatusWebSocket();
//     }

//     if (window.location.pathname === "/dashboard/users/users-list/") {
//         fetchUsers();
//     }

//     if (window.location.pathname === "api/login/") {
//         console.log('cu')

//     }



//     const registerForm = document.getElementById("register-form");
//     if (registerForm) registerForm.addEventListener("submit", registerUser);

//     const guestForm = document.getElementById("guest-form");
//     if (guestForm) guestForm.addEventListener("submit", registerGuest);
// });



import { fetchDashboardData, fetchUsers, logoutUser , showDVA , showSPOT } from "./dashboard.js";
import {  registerUser, registerGuest } from "./auth.js";
import { initUserStatusWebSocket } from "./websocket.js";

document.addEventListener("DOMContentLoaded", () => {


    if (window.location.pathname === "/dashboard/") {
        initUserStatusWebSocket();
        fetchDashboardData();
        showDVA();
        showSPOT();
    }

    if (window.location.pathname === "/dashboard/users/users-list/") {
        fetchUsers();
    }

    if (window.location.pathname === "api/login/") {
        console.log('cu')
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", logoutUser);
    }

    const userListBtn = document.getElementById("user-list-button");
    if (userListBtn) {
        userListBtn.addEventListener("click", fetchUsers);
    }



    const registerForm = document.getElementById("register-form");
    if (registerForm) registerForm.addEventListener("submit", registerUser);

    const guestForm = document.getElementById("guest-form");
    if (guestForm) guestForm.addEventListener("submit", registerGuest);



});

