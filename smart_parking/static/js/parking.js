import { scheduleStaticTokenRefresh } from "./utils.js";
let areaCam = 1;
var w, h;
var parklist = Array(14).fill(0);

function setupparkingmanager() {
  w = document.getElementById("parkingspace").offsetWidth;
  h = document.getElementById("parkingspace").offsetHeight;
}

function Areachange(number) {
  for (let i = 0; i < parklist.length; i++) {
    if (parklist[i] === 1) {
      carexit(i);
    }
  }
  parklist = Array(14).fill(0);
  areaCam = number;
  document.getElementById("title-area").innerText =
    "PARKING MANAGER Area " + number + " (3s)";
  const titleArea = document.getElementById("title-area");
  let countdown = 2;

  const intervalId = setInterval(() => {
    if (countdown > 0) {
      titleArea.innerText = `PARKING MANAGER Area ${number} (${countdown}s)`;
      countdown--;
    } else {
      titleArea.innerText = `PARKING MANAGER Area ${number}`;
      clearInterval(intervalId);
    }
  }, 1000);
}

async function fetchAreas() {
  const res = await fetch("/parking/areas/");
  const areas = await res.json();
  console.log("Starting to fetch areas...");

  areas.forEach((area) => {
    const wschema = window.location.protocol === "https:" ? "wss" : "ws";

    const socket = new WebSocket(
      `${wschema}://${window.location.host}/ws/video/${area}/`
    );

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);

      if (area == areaCam) {
        if (data.spot_details) {
          data.spot_details.forEach((spot) => {
            console.log("Area 1 here");
            let number = spot.spot.match(/\d+/)[0] - 1;
            const slot = parseInt(number);
            const isOccupied = spot.status === "occupied";
            parklist[slot] = isOccupied ? 1 : 0;

            if (isOccupied && !document.getElementById("car" + slot)) {
              carenter(slot);
            } else if (!isOccupied && document.getElementById("car" + slot)) {
              carexit(slot);
            }
          });
        }
      }
    };
    socket.onopen = () => console.log(`Connected to area ${area}`);
    socket.onclose = () => console.log(`Disconnected from area ${area}`);
  });
}

function carexit(slot) {
  parklist[slot] = 0;
  console.log(parklist);
  document.getElementById("slot" + (slot + 1).toString()).style.background =
    "rgb(27,118,19)";
  if (slot <= 6) {
    document.getElementById(
      "car" + slot.toString()
    ).style.animation = `car-exit-top-${slot} 2s both`;
  } else {
    document.getElementById(
      "car" + slot.toString()
    ).style.animation = `car-exit-bottom-${slot} 2s both`;
  }

  setTimeout(function () {
    document.getElementById("car" + slot.toString()).remove();
  }, 2000);
}

function generatenewcar(slot) {
  const space = document.getElementById("parkingspace");
  const img = document.createElement("img");
  img.src = window.CAR_IMAGE_URL;
  img.className = "new-car-origin";
  img.id = "car" + slot.toString();
  img.style.width = w * 0.2 + "px";

  const anim = document.createElement("style");

  let verticalOffset;
  let rotation = "90deg";

  if (slot <= 6) {
    // Left-side slots (0–4)
    img.style.left = "12%";
    verticalOffset = h * (0.1 + 0.11 * (6 - slot));
    if (slot == 6) {
      verticalOffset += h * 0.0012;
    }

    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${slot} {
        0% { 
          transform: translate(0, 0) rotate(0deg); 
        }
        70% { 
          transform: translate(0, -${verticalOffset}px) rotate(0deg); 
        }
        80% { 
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}); 
        }
        to { 
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -110%); 
        }
      }`
    );

    anim.appendChild(rule);
    const exitAnim = document.createTextNode(`
      @-webkit-keyframes car-exit-top-${slot} {
        from{
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -110%); 
        }
        60% {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -110%) translate(0, 110%); ; 
        }
        80% {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -110%) translate(0, 110%) rotate(${rotation});  
        }
        to {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -110%) translate(0, 110%) rotate(${rotation}) translate(0, -${verticalOffset}px);  
        }
      }
    `);

    anim.appendChild(exitAnim);
  } else {
    // Right-side slots (5–9)
    img.style.right = "12%";
    verticalOffset = h * (0.1 + 0.11 * (13 - slot));
    if (slot == 13) {
      verticalOffset += h * 0.0012;
    }
    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${slot} {
        0% { transform: translateY(0) rotate(0deg); }
        70% { transform: translateY(-${verticalOffset}px) rotate(0deg); }
        80% { transform: translateY(-${verticalOffset}px) rotate(-90deg); }
        100% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-110%);}
      }`
    );
    anim.appendChild(rule);
    const exitAnim = document.createTextNode(
      `@-webkit-keyframes car-exit-bottom-${slot} {
        0% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-110%); }
        60% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-110%) translateY(110%);}
        80% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-110%)  translateY(110%) rotate(-${rotation}); }
        100% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-110%) translateY(110%) rotate(-${rotation}) translateY(-${verticalOffset}px);}
      }`
    );

    anim.appendChild(exitAnim);
  }

  document.head.appendChild(anim);
  space.appendChild(img);
}

function carenter(slot) {
  if (!document.getElementById("car" + slot.toString())) {
    parklist[slot] = 1;
    console.log(parklist);
    generatenewcar(slot);
    document.getElementById("slot" + (slot + 1).toString()).style.background =
      "rgb(146,18,18)";
    if (slot != 6 && slot != 13)
      document.getElementById("car" + slot.toString()).style.right =
        -w +
        w * 0.04 +
        (5 - ((slot + 1) % 5)) * (w * 0.8 * 0.2) +
        w * 0.8 * 0.05 +
        "px";
    else
      document.getElementById("car" + slot.toString()).style.right =
        -w + w * 0.04 + w * 0.8 * 0.05 + "px";
    if (slot <= 6)
      document.getElementById(
        "car" + slot.toString()
      ).style.animation = `car-park-${slot} 2s both`;
    else
      document.getElementById(
        "car" + slot.toString()
      ).style.animation = `car-park-${slot} 2s both`;
  } else {
    carexit(slot);
  }
}
window.carenter = carenter;
window.carexit = carexit;
window.setupparkingmanager = setupparkingmanager;
window.fetchAreas = fetchAreas;
window.generatenewcar = generatenewcar;
window.Areachange = Areachange;

document.addEventListener("DOMContentLoaded", async () => {
  scheduleStaticTokenRefresh();
  await fetchAreas();
});
