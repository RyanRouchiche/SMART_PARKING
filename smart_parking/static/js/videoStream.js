export async  function fetchFloors() {
    const res = await fetch('/parking/api/floors/');
    const floors = await res.json(); 

    const container = document.getElementById('floors-container');
    container.innerHTML = "";  

    floors.forEach(floor => {
        // Create floor section
        const floorDiv = document.createElement('div');
        floorDiv.classList.add('floor-section');
        floorDiv.innerHTML = `
            <h3>Étage ${floor} - Places Disponibles: <span id="count-${floor}">0</span></h3>
            <img id="video-${floor}" class="floor-video" src="" />
            <div id="spot-info-${floor}" class="spot-info">Chargement des places...</div>
        `;
        container.appendChild(floorDiv);

        // Start WebSocket connection for this floor
        const socket = new WebSocket(`ws://${window.location.host}/ws/video/${floor}/`);

        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.video_frame) {
                document.getElementById(`video-${floor}`).src = "data:image/jpeg;base64," + data.video_frame;
            }
            if (data.available_spots !== undefined) {
                document.getElementById(`count-${floor}`).innerText = data.available_spots;
            }
            if (data.spot_details) {
                let spotInfo = "Détails des places :<br>";
                data.spot_details.forEach((spot, index) => {
                    spotInfo += `Place ${index + 1}: ${spot.status} <br>`;
                });
                document.getElementById(`spot-info-${floor}`).innerHTML = spotInfo;
            }
        };

        socket.onopen = () => console.log(`Connected to floor ${floor}`);
        socket.onclose = () => console.log(`Disconnected from floor ${floor}`);
    });
}

// Call fetchFloors on page load
window.addEventListener("DOMContentLoaded", fetchFloors);
