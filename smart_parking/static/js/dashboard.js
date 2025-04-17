import { getCookie, postJSON } from "./utils.js";

export async function fetchDashboardData() {
    const response = await fetch("/dashboard/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
    });

    const data = await response.json();
    if (data.success) {
        document.getElementById("username").innerText = data.user.username;
        document.getElementById("email").innerText = data.user.email;
        document.getElementById("role").innerText = data.user.role;
        document.getElementById("user-id").innerText = data.user.id;
    } else {
        alert("You are not authenticated. Please log in.");
        window.location.href = "api/login/";
    }
}

export async function fetchUsers() {
    try {
        const response = await fetch("/dashboard/users/users-list/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
        });
        const data = await response.json();
        populateUserTable(data.users);
    } catch (error) {
        console.error("User fetch error:", error);
    }
}

function populateUserTable(users) {
    const tableBody = document.getElementById("user-table-body");
    if (!tableBody) return;

    tableBody.innerHTML = "";
    users.forEach(user => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.email}</td>
            <td>${user.first_name}</td>
            <td>${user.last_name}</td>
            <td id="status-${user.id}">${user.status}</td>
            <td><button onclick="deleteUser(${user.id})">Delete</button></td>
        `;
        tableBody.appendChild(row);
    });
}

export async function deleteUser(userId) {
    if (confirm("Are you sure you want to delete this user?")) {
        try {
            const response = await fetch(`/dashboard/users/${userId}/delete/`, {
                method: "DELETE",
                headers: {
                    "X-CSRFToken": getCookie("csrftoken"),
                },
            });

            if (response.ok) {
                alert("User deleted successfully.");
                fetchUsers();
            } else {
                const data = await response.json();
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error("Delete user error:", error);
        }
    }
}

export function logoutUser() {
    
    document.cookie = 'access_token=; Max-Age=0; path=/; domain=' + window.location.hostname;
    document.cookie = 'refresh_token=; Max-Age=0; path=/; domain=' + window.location.hostname;

  
    fetch('/api/logout/', {
        method: 'POST',
        credentials: 'include',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
    .then(response => {
        if (response.ok) {
            console.log('Déconnexion réussie');
         
            window.location.href = '/api/login/';
        } else {
            console.error('Erreur de déconnexion');
        }
    })
    .catch(error => {
        console.error('Erreur lors de la déconnexion :', error);
    });
}
