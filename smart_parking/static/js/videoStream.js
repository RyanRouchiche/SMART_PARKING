import { scheduleStaticTokenRefresh } from "./utils.js";


async  function fetchAreas() {
    const res = await fetch('/parking/areas/');
    const areas = await res.json(); 

    const container = document.getElementById('areas-container');
    container.innerHTML = "";  

    areas.forEach(area => {
     
        const areaDiv = document.createElement('div');
        areaDiv.classList.add('area-section');
        areaDiv.innerHTML = `
            <h3>Étage ${area} - Places Disponibles: <span id="count-${area}">0</span></h3>
            <img id="video-${area}" class="area-video" src="" />
            <div id="spot-info-${area}" class="spot-info">Chargement des places...</div>
        `;
        container.appendChild(areaDiv);


        const wschema = window.location.protocol === "https:" ? "wss" : "ws";

        
        const socket = new WebSocket(`${wschema}://${window.location.host}/ws/video/${area}/`);

        socket.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.video_frame) {
                document.getElementById(`video-${area}`).src = "data:image/jpeg;base64," + data.video_frame;
            }
            if (data.available_spots !== undefined) {
                document.getElementById(`count-${area}`).innerText = data.available_spots;
            }
            if (data.spot_details) {
                let spotInfo = "Détails des places :<br>";
                data.spot_details.forEach((spot, index) => {
                    spotInfo += `Place ${spot.spot}: ${spot.status} <br>`;
                    console.log(`Place ${spot.spot}: ${spot.status}`); // Log the spot status
                });
                document.getElementById(`spot-info-${area}`).innerHTML = spotInfo;
            }
        };

        socket.onopen = () => console.log(`Connected to area ${area}`);
        socket.onclose = () => console.log(`Disconnected from area ${area}`);
    });
}


document.addEventListener("DOMContentLoaded", async  () => {
    scheduleStaticTokenRefresh(); 
    await fetchAreas();
    
});

