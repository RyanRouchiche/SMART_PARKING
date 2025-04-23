let selectedPoints = {}; // Store the selected points for each floor

function selectPoint(event, floor) {
    if (!selectedPoints[floor]) {
        selectedPoints[floor] = [];
    }

    let imgContainer = document.getElementById(`container-${floor}`);
    let rect = imgContainer.getBoundingClientRect();
    let x = event.clientX - rect.left;
    let y = event.clientY - rect.top;

    let currentSpot = selectedPoints[floor].length > 0 ? selectedPoints[floor][selectedPoints[floor].length - 1] : null;
    if (!currentSpot || Object.values(currentSpot)[0].length === 4) {
        selectedPoints[floor].push({ "Unnamed Spot": [] });
        currentSpot = selectedPoints[floor][selectedPoints[floor].length - 1];
    }

    Object.values(currentSpot)[0].push([x, y]);

    let dot = document.createElement("div");
    dot.classList.add("selected-point");
    dot.style.left = `${x}px`;
    dot.style.top = `${y}px`;
    imgContainer.appendChild(dot);

    if (Object.values(currentSpot)[0].length === 4) {
        let spotName = prompt("Entrez le nom ou l'identifiant de la place de parking (ex: Spot 1):");
        if (!spotName) {
            alert("Vous devez entrer un nom pour la place de parking.");
            spotName = `Spot ${selectedPoints[floor].length}`;
        }
        let points = Object.values(currentSpot)[0];
        delete currentSpot["Unnamed Spot"];
        currentSpot[spotName] = points;

        alert(`Vous avez terminé la sélection pour ${spotName} à l'étage ${floor}.`);
    }
}

function sendCoordinates() {
    const csrfToken = document.querySelector("meta[name='csrf-token']").getAttribute("content");

    const formattedData = Object.keys(selectedPoints).map(floor => {
        const coordinates = {};
        selectedPoints[floor].forEach(spot => {
            const spotName = Object.keys(spot)[0];
            coordinates[spotName] = spot[spotName].map(point => point.map(coord => Math.round(coord)));
        });
        return {
            floor: floor.toString(),
            coordinates: coordinates
        };
    });

    fetch("/parking/api/saveSpotCoordinates/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken
        },
        body: JSON.stringify(formattedData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Erreur lors de l'enregistrement des coordonnées.");
        }
        return response.json();
    })
    .then(data => {
        alert(data.message);
        selectedPoints = {};
    })
    .catch(error => alert("Erreur : " + error.message));
}
