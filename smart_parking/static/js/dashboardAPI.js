document.addEventListener("DOMContentLoaded", function () {
    const userStatusSocket = new WebSocket(
        `ws://${window.location.host}/ws/user-status/` 
    );

    console.log("WebSocket URL:", userStatusSocket.url);



    userStatusSocket.onopen = function () {
        console.log("WebSocket connection established.");
    };

    userStatusSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        const statusElement = document.getElementById(`status-${data.user_id}`);
        if (statusElement) {
            console.log('status')
            statusElement.innerText = data.status; 
        }
    };
    fetch("/dashboard/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken"),
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Display the user data on the page
            document.getElementById("username").innerText = data.user.username;
            document.getElementById("email").innerText = data.user.email;
            document.getElementById("role").innerText = data.user.role;
            document.getElementById("user-id").innerText = data.user.id;
        } else {
            alert("You are not authenticated. Please log in.");
            window.location.href = "/api/login/";
        }
    })
    .catch(error => {
        console.error("Error fetching data:", error);
        alert("An error occurred. Please try again later.");
    });

    // Logout functionality
    const logoutbutton = document.getElementById("logout-btn") ; 
    if (logoutbutton){
        console.log('Logout button found!');
        logoutbutton.addEventListener("click", function () {
         
                fetch("/api/logout/", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-CSRFToken": getCookie("csrftoken"),
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message); 
                        window.location.href = "/api/login/"; 
                    } else {
                        alert("Logout failed: " + data.error); 
                    }
                })
                .catch(error => {
                    console.error("Error logging out:", error);
                    alert("An error occurred while logging out. Please try again.");
                });
            });

    }
    else {
        console.error("Logout button not found!");
    }



    // userStatusSocket.onclose = function () {
    //     console.log("WebSocket connection closed.");
    // };

    userStatusSocket.onerror = function (error) {
        console.error("WebSocket error:", error);
    };

    // Function to get the CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            let cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const userlistbutton = document.getElementById("user-list-button") ; 
    if (userlistbutton) {
        console.log('User list button found!');
        userlistbutton.addEventListener("click", function () {
            window.location.href = "/dashboard/users/users-list/";
        });
    }else {
        console.error("User list button not found!");
    }
    if (window.location.pathname === "/dashboard/users/users-list/") {
            fetchUsers(); 
    }

    // const DVAbutton = document.getElementById("video_feed") ;
    // if (DVAbutton) {
    //     console.log('DVA button found!');
    //     DVAbutton.addEventListener("click", function () {
    //         window.location.href = "/parking/api/video/";
    //     });
    // }

    // const spotbutton = document.getyElementById("markSpot") ;
    // if (spotbutton) {
    //     console.log('Spot button found!');
    //     spotbutton.addEventListener("click", function () {
    //         window.location.href = "/parking/api/pickupSpot/";
    //     });
    // }
    
    function populateUserTable(users) {
        const tableBody = document.getElementById('user-table-body');
        if (!tableBody) {
            console.error('Table body element not found!');
            return;
        }
    
        tableBody.innerHTML = ''; 
        users.forEach(user => {
            const row = document.createElement('tr');
    
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.first_name}</td>
                <td>${user.last_name}</td>
                <td id="status-${user.id}">${user.status}</td>
                <td>
                    <button onclick="deleteUser(${user.id})">Delete</button>
                </td>
            `;
            tableBody.appendChild(row);
        });
    }

    async function fetchUsers() {
        console.log("fetchUsers called");
        try {
            const response = await fetch('/dashboard/users/users-list/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });

            if (response.ok) {
                const data = await response.json();
                populateUserTable(data.users); 
            } else {
                console.error('Failed to fetch users:', await response.json());
                alert('Failed to fetch users. Please try again.');
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            alert('An error occurred while fetching users.');
        }
    }


    async function deleteUser(userId) {
        if (confirm('Are you sure you want to delete this user?')) {
            try {
                const response = await fetch(`/dashboard/users/${userId}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                });

                if (response.ok) {
                    alert('User deleted successfully.');
                    fetchUsers(); // Refresh the user list
                } else {
                    const data = await response.json();
                    alert(`Error: ${data.error}`);
                }
            } catch (error) {
                console.error('Error deleting user:', error);
                alert('An error occurred. Please try again.');
            }
        }
    }
});
