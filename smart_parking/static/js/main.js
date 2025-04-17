import { fetchDashboardData, fetchUsers } from "./dashboard.js";
import { loginUser, registerUser, registerGuest } from "./auth.js";
import { initUserStatusWebSocket } from "./websocket.js";

document.addEventListener("DOMContentLoaded", () => {
    if (window.location.pathname === "/dashboard/") {
        fetchDashboardData();
        initUserStatusWebSocket();
    }

    if (window.location.pathname === "/dashboard/users/users-list/") {
        fetchUsers();
    }

    const loginForm = document.getElementById("login-form");
    if (loginForm) loginForm.addEventListener("submit", loginUser);

    const registerForm = document.getElementById("register-form");
    if (registerForm) registerForm.addEventListener("submit", registerUser);

    const guestForm = document.getElementById("guest-form");
    if (guestForm) guestForm.addEventListener("submit", registerGuest);
});
