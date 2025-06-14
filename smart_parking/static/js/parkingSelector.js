import { sendrequest, postrequest } from "./utils.js";
let currentLanguage, Undo;
let selectedPoints = {}; // Store the selected points for each floor

function getRectanglePointsFromTwoPoints(p1, p2) {
  const x1 = Math.min(p1[0], p2[0]);
  const y1 = Math.min(p1[1], p2[1]);
  const x2 = Math.max(p1[0], p2[0]);
  const y2 = Math.max(p1[1], p2[1]);

  return [
    [x1, y1],
    [x2, y1],
    [x2, y2],
    [x1, y2],
  ];
}

// Right-click to delete rectangle
function handleRightClickOnRectangle(event) {
  event.preventDefault();

  const rectangle = event.currentTarget;
  const spotName = rectangle.getAttribute("data-spot-name");
  const area = rectangle.getAttribute("data-area");

  if (!spotName || !area || !selectedPoints[area]) return;

  selectedPoints[area] = selectedPoints[area].filter(
    (spot) => !spot.hasOwnProperty(spotName)
  );

  rectangle.remove();

  const container = document.getElementById(`container-${area}`);
  const dots = container.querySelectorAll(
    `.selected-point[data-spot-name="${spotName}"]`
  );
  dots.forEach((dot) => dot.remove());
  Undo.style.display = "block";
  currentLanguage = getCurrentLanguage();
  const deletedmsg =
    currentLanguage === "en"
      ? `Spot "${spotName}" deleted.`
      : `Place  ${spotName} supprimée`;
  showConfirmModal(deletedmsg);
}

async function selectPoint(event, area) {
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
  dot.setAttribute("data-temp", "true");
  imgContainer.appendChild(dot);

  if (Object.values(currentSpot)[0].length === 2) {
    const [p1, p2] = Object.values(currentSpot)[0];
    const fullPoints = getRectanglePointsFromTwoPoints(p1, p2);

    Object.values(currentSpot)[0].length = 0;
    fullPoints.forEach((pt) => Object.values(currentSpot)[0].push(pt));

    const existingNames = selectedPoints[area].map(
      (spot) => Object.keys(spot)[0]
    );
    let spotName = await getSpotNameFromModal();

    if (!spotName) {
      let counter = 1;
      while (existingNames.includes(`Spot ${counter}`)) {
        counter++;
      }
      spotName = `Spot ${counter}`;
    }

    const points = Object.values(currentSpot)[0];
    selectedPoints[area].pop();

    const tempDots = imgContainer.querySelectorAll('[data-temp="true"]');
    tempDots.forEach((dot) => dot.remove());

    renderSpot(area, spotName, points);
    Undo.style.display = "block";
    currentLanguage = getCurrentLanguage();
    const Selectedmsg =
      currentLanguage === "en"
        ? `Spot selected: ${spotName} in area ${area}.`
        : `Place sélectionnée : ${spotName} dans la zone ${area}`;
    showConfirmModal(Selectedmsg);
  }
}

async function sendCoordinates() {
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

  const res = await postrequest(
    "/parking/saveSpotCoordinates/",
    "POST",
    formattedData
  );
  currentLanguage = getCurrentLanguage();
  if (res.status === 201) {
    const msgSuccees =
      currentLanguage === "en"
        ? "Coordinates saved successfully!."
        : "Coordonnées enregistrées avec succès !";
    showConfirmModal(msgSuccees);
  } else {
    const msgError =
      currentLanguage === "en"
        ? "Error saving coordinates."
        : "Erreur lors de l’enregistrement des coordonnées.";
    showConfirmModal(msgError);
  }
  clearAllSpots();
}

async function loadCoordinates() {
  try {
    const res = await sendrequest("/parking/coordinates/", "GET");
    console.log("response : ", res);

    if (!res.ok) {
      console.log("erreur loading json file");
    }

    const result = res.data;

    console.log("result : ", result);

    console.log("Coordinates:", result.data);
    result.data.forEach((areaObj) => {
      const area = areaObj.area;
      const coordinates = areaObj.coordinates;

      Object.entries(coordinates).forEach(([spotName, points]) => {
        renderSpot(area, spotName, points);
      });
    });
  } catch (error) {
    console.error("Error loading coordinates:", error);
  }
}

function renderSpot(area, spotName, points) {
  const container = document.getElementById(`container-${area}`);
  if (!container) return;
  if (!selectedPoints[area]) {
    selectedPoints[area] = [];
  }
  // Add spot to selectedPoints
  selectedPoints[area].push({ [spotName]: points });

  // Draw dots
  points.forEach(([x, y]) => {
    const dot = document.createElement("div");
    dot.classList.add("selected-point");
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    dot.setAttribute("data-spot-name", spotName);
    container.appendChild(dot);
  });

  // Calculate rectangle dimensions
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  const width = maxX - minX;
  const height = maxY - minY;

  // Draw rectangle
  const rectangle = document.createElement("div");
  rectangle.classList.add("spot-rectangle");
  rectangle.style.left = `${minX}px`;
  rectangle.style.top = `${minY}px`;
  rectangle.style.width = `${width}px`;
  rectangle.style.height = `${height}px`;
  rectangle.innerText = spotName;
  rectangle.setAttribute("data-spot-name", spotName);
  rectangle.setAttribute("data-area", area);
  rectangle.addEventListener("contextmenu", handleRightClickOnRectangle);
  container.appendChild(rectangle);
}

//undo all changes
function clearAllSpots() {
  Undo.style.display = "none";
  document
    .querySelectorAll(".selected-point, .spot-rectangle")
    .forEach((el) => el.remove());
  selectedPoints = {};
  loadCoordinates();
}

function getSpotNameFromModal() {
  return new Promise((resolve) => {
    const modal = document.getElementById("InputModal");
    const inputField = document.getElementById("inputField");
    const confirmButton = document.getElementById("confirmButton");

    inputField.value = "";

    modal.style.display = "flex";

    function cleanup() {
      confirmButton.removeEventListener("click", onConfirm);
      modal.style.display = "none";
    }

    function onConfirm() {
      const value = inputField.value.trim();
      cleanup();
      resolve(value || null);
    }
    confirmButton.addEventListener("click", onConfirm);
  });
}

window.selectPoint = selectPoint;
window.sendCoordinates = sendCoordinates;
window.clearAllSpots = clearAllSpots;
window.handleRightClickOnRectangle = handleRightClickOnRectangle;

document.addEventListener("DOMContentLoaded", async () => {
  currentLanguage = getCurrentLanguage();
  Undo = document.getElementById("Undo");
  loadCoordinates();
});
