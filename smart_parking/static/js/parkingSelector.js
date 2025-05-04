let selectedPoints = {}; // Store the selected points for each floor

function selectPoint(event, area) {
    if (!selectedPoints[area]) {
        selectedPoints[area] = [];
    }

    let imgContainer = document.getElementById(`container-${area}`);
    let rect = imgContainer.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    let currentSpot = selectedPoints[area].length > 0 ? selectedPoints[area][selectedPoints[area].length - 1] : null;
    if (!currentSpot || Object.values(currentSpot)[0].length === 4) {
        selectedPoints[area].push({ "Unnamed Spot": [] });
        currentSpot = selectedPoints[area][selectedPoints[area].length - 1];
    }

    Object.values(currentSpot)[0].push([x, y]);

    let dot = document.createElement("div");
    dot.classList.add("selected-point");
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    imgContainer.appendChild(dot);

    if (Object.values(currentSpot)[0].length === 4) {
        let spotName = prompt("pick a name for the spot ex : spot 1");
        if (!spotName) {
            alert("put  a  name for parking spot");
            spotName = `Spot ${selectedPoints[area].length}`;
        }
        let points = Object.values(currentSpot)[0];
        delete currentSpot["Unnamed Spot"];
        currentSpot[spotName] = points;

        alert(`spot selected  ${spotName} area ${area}.`);
    }
}

function sendCoordinates() {
    const csrfToken = document.querySelector("meta[name='csrf-token']").getAttribute("content");

    const formattedData = Object.keys(selectedPoints).map(area => {
        const coordinates = {};
        selectedPoints[area].forEach(spot => {
            const spotName = Object.keys(spot)[0];
            coordinates[spotName] = spot[spotName].map(point => point.map(coord => Math.round(coord)));
        });
        return {
            area: area.toString(),
            coordinates: coordinates
        };
    });

    fetch("/parking/saveSpotCoordinates/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(formattedData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("eerror saving coordinates");
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        selectedPoints = {};
    })
    .catch(error => alert("Erreur : " + error.message));
}

function scheduleStaticTokenRefresh() {
    setInterval(() => {
      console.log("Proactively refreshing token...");

      fetch("/auth/token/refresh/", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then(response => {
          if (!response.ok) {
            console.warn("Token refresh failed. Redirecting to login...");
            window.location.href = "/auth/login/";
          } else {
            console.log("Token successfully refreshed.");
          }
        })
        .catch(error => {
          console.error("Token refresh error:", error);
          window.location.href = "/auth/login/";
        });

    }, 58000); 
  }

document.addEventListener("DOMContentLoaded", function () {
    scheduleStaticTokenRefresh();

    });