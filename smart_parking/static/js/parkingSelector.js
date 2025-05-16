let selectedPoints = {}; // Store the selected points for each floor

function getRectanglePointsFromTwoPoints(p1, p2) {
  const x1 = Math.min(p1[0], p2[0]);
  const y1 = Math.min(p1[1], p2[1]);
  const x2 = Math.max(p1[0], p2[0]);
  const y2 = Math.max(p1[1], p2[1]);

  return [
    [x1, y1], // top-left
    [x2, y1], // top-right
    [x2, y2], // bottom-right
    [x1, y2], // bottom-left
  ];
}

function selectPoint(event, area) {
  if (!selectedPoints[area]) {
    selectedPoints[area] = [];
  }

  let imgContainer = document.getElementById(`container-${area}`);
  let rect = imgContainer.getBoundingClientRect();
  let x = event.clientX - rect.left;
  let y = event.clientY - rect.top;

  let currentSpot =
    selectedPoints[area].length > 0
      ? selectedPoints[area][selectedPoints[area].length - 1]
      : null;

  if (
    !currentSpot ||
    !currentSpot.hasOwnProperty("Unnamed Spot") ||
    currentSpot["Unnamed Spot"].length === 2
  ) {
    selectedPoints[area].push({ "Unnamed Spot": [] });
    currentSpot = selectedPoints[area][selectedPoints[area].length - 1];
  }

  Object.values(currentSpot)[0].push([x, y]);

  let dot = document.createElement("div");
  dot.classList.add("selected-point");
  dot.style.left = `${x}px`;
  dot.style.top = `${y}px`;
  imgContainer.appendChild(dot);

  if (Object.values(currentSpot)[0].length === 2) {
    const [p1, p2] = Object.values(currentSpot)[0];
    const fullPoints = getRectanglePointsFromTwoPoints(p1, p2);

    // Replace the 2 points with the 4 full rectangle points
    Object.values(currentSpot)[0].length = 0;
    fullPoints.forEach((pt) => Object.values(currentSpot)[0].push(pt));

    let spotName = prompt("Pick a name for the spot (e.g., Spot 1)");
    if (!spotName) {
      alert("Please provide a name for the parking spot.");
      spotName = `Spot ${selectedPoints[area].length}`;
    }

    const points = Object.values(currentSpot)[0];
    delete currentSpot["Unnamed Spot"];
    currentSpot[spotName] = points;

    // Draw rectangle
    const xs = points.map((p) => p[0]);
    const ys = points.map((p) => p[1]);
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    const maxX = Math.max(...xs);
    const maxY = Math.max(...ys);
    const width = maxX - minX;
    const height = maxY - minY;

    let rectangle = document.createElement("div");
    rectangle.classList.add("spot-rectangle");
    rectangle.style.left = `${minX}px`;
    rectangle.style.top = `${minY}px`;
    rectangle.style.width = `${width}px`;
    rectangle.style.height = `${height}px`;
    rectangle.innerText = spotName;
    imgContainer.appendChild(rectangle);

    alert(`Spot selected: ${spotName} in area ${area}.`);
  }
}

function sendCoordinates() {
  const csrfToken = document.querySelector(
    'input[name="csrfmiddlewaretoken"]'
  ).value;

  const formattedData = Object.keys(selectedPoints).map((area) => {
    const coordinates = {};
    selectedPoints[area].forEach((spot) => {
      const spotName = Object.keys(spot)[0];
      coordinates[spotName] = spot[spotName].map((point) =>
        point.map((coord) => Math.round(coord))
      );
    });
    return {
      area: area.toString(),
      coordinates: coordinates,
    };
  });

  fetch("/parking/saveSpotCoordinates/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(formattedData),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("error saving coordinates");
      }
      return response.json();
    })
    .then((data) => {
      alert(data.message);
      selectedPoints = {};
    })
    .catch((error) => alert("Erreur : " + error.message));
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
      .then((response) => {
        if (!response.ok) {
          console.warn("Token refresh failed. Redirecting to login...");
          window.location.href = "/auth/login/";
        } else {
          console.log("Token successfully refreshed.");
        }
      })
      .catch((error) => {
        console.error("Token refresh error:", error);
        window.location.href = "/auth/login/";
      });
  }, 58000);
}

document.addEventListener("DOMContentLoaded", function () {
  scheduleStaticTokenRefresh();
});
