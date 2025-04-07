async function loginUser(event) {
    event.preventDefault(); // Prevent form submission

    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/login/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, password }),
        });

        const data = await response.json();
        if (response.ok) {
            alert("Login successful!");
            window.location.href = "/dashboard/"; 
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("An error occurred. Please try again.");
    }
}



function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(";").shift();
}

function setCookie(name, value, maxAge) {
    document.cookie = `${name}=${value}; Max-Age=${maxAge}; Path=/; Secure; SameSite=None; HttpOnly`;
}

async function refreshAccessToken() {
    try {
        const response = await fetch("/api/token/refresh/", {
            method: "POST",
            credentials: "include",
        });

        if (response.ok) {
            const data = await response.json();
            setCookie("access_token", data.access, 10 * 60); 
            return true;
        } else {
            console.error("Failed to refresh access token");
            return false;
        }
    } catch (error) {
        console.error("Error refreshing access token:", error);
        return false;
    }
}


async function fetchData(endpoint) {
    const accessToken = getCookie("access_token");

    try {
        const response = await fetch(endpoint, {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${accessToken}`,
            },
        });

        if (response.status === 401) {
            const refreshSuccess = await refreshAccessToken();
            if (refreshSuccess) {
                return fetchData(endpoint); 
            } else {
                throw new Error("Failed to refresh access token");
            }
        }

        const data = await response.json();
        return data;
        console.log("Data fetched successfully:", data);
    } catch (error) {
        console.error("Error fetching data:", error);
        throw error;
    }
}