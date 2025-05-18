import { sendrequest, initwebsocketconn } from "./utils.js";

let socket = null;
let LCD_AREA = null;

async function setAreas() {
  try {
    const res = await sendrequest('/parking/areas/', 'GET');
    console.log('Réponse reçue :', res);

    const areas = res.data;

    if (!Array.isArray(areas)) {
      console.error("Format de réponse inattendu :", areas);
      return;
    }

    const select = document.getElementById("areaSelect");
    areas.forEach(area => {
      const option = document.createElement("option");
      option.value = area;
      option.textContent = area;
      select.appendChild(option);
    });

    LCD_AREA = areas[0];
    select.value = LCD_AREA;
    document.getElementById("title").textContent = `Zone : ${LCD_AREA}`;

    DisplaySpotStatus(LCD_AREA);

    select.addEventListener("change", () => {
      LCD_AREA = parseInt(select.value);
      document.getElementById("title").textContent = `Zone : ${LCD_AREA}`;
      if (socket) socket.close();
      DisplaySpotStatus(LCD_AREA);
    });
  } catch (err) {
    console.error("Erreur lors de la récupération des zones :", err);
  }
}

function DisplaySpotStatus(area) {
  const wschema = window.location.protocol === "https:" ? "wss" : "ws";
  socket = initwebsocketconn(wschema, `ws/video/${area}/`);
  console.log("Connexion WebSocket ouverte :", socket.url);

  socket.onmessage = event => {
    const data = JSON.parse(event.data);
    console.log("Message WebSocket :", data);

    if (parseInt(data.area) === LCD_AREA) {
      const emptySpots = data.spot_details.filter(spot => spot.status === "empty");
      document.getElementById("count").textContent = emptySpots.length;

      const list = document.getElementById("spots");
      list.innerHTML = "";

      emptySpots.forEach(spot => {
        const match = spot.spot.match(/\d+/);
        const spotNum = match ? parseInt(match[0]) : 0;
        const arrow = spotNum % 2 === 0 ? "→" : "←";

        const li = document.createElement("li");
        li.innerHTML = `${spot.spot} <span class="arrow">${arrow}</span>`;
        list.appendChild(li);
      });
    }
  };

  socket.onerror = err => console.error("Erreur WebSocket :", err);
}

document.addEventListener("DOMContentLoaded", setAreas);
