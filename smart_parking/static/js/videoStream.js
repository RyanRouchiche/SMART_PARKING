import { sendrequest, initwebsocketconn } from "./utils.js";

let swiper, w, h;
let areaLength;
const indexToAreaIdMap = {};
let MaxareaTop = 0;
const spotNameToIndexMap = {};
let socket = null;

//calls
const areaList = document.getElementById("area-list");
const swiperWrapper = document.getElementById("swiper-wrapper");
const items = document.querySelectorAll("#area-list li");
const sidebar = document.getElementById("sidebar");
const open = document.getElementById("open");
const arrow = document.getElementById("arrow");

open.addEventListener("click", () => {
  sidebar.classList.toggle("close");
  arrow.innerHTML = sidebar.classList.contains("close")
    ? "&lt;&lt;"
    : "&gt;&gt;";
});

// Function to handle token refresh +  dynamic div creation based on websocket data
document.addEventListener("DOMContentLoaded", async () => {
  let currentLanguage = localStorage.getItem("language");
  if (!currentLanguage) {
    currentLanguage = document.documentElement.lang || "en";
  }
  const res = await sendrequest("/parking/areas/", "GET");
  const areas = await res.data;

  areas.forEach((areaId, index) => {
    indexToAreaIdMap[index] = areaId;
    const li = document.createElement("li");
    li.textContent =
      currentLanguage == "en" ? `Area ${areaId}` : `Zone ${areaId}`;
    li.dataset.index = index;
    if (index === 0) li.classList.add("active");

    li.addEventListener("click", () => {
      const listItems = document.querySelectorAll("li");
      listItems.forEach((item) => item.classList.remove("active"));
      li.classList.add("active");
      swiper.slideTo(index);
    });

    areaList.appendChild(li);

    const slide = document.createElement("div");
    slide.classList.add("swiper-slide");
    slide.id = `slide-${areaId}`;

    const title = document.createElement("div");
    title.classList.add("area-title");
    title.textContent =
      currentLanguage == "en" ? `Area ${areaId}` : `Zone ${areaId}`;
    slide.appendChild(title);

    const spotLabel = document.createElement("div");
    spotLabel.classList.add("available-spots");
    spotLabel.id = `available-${areaId}`;
    console.log(currentLanguage);
    spotLabel.textContent =
      currentLanguage == "en" ? "Available spots : ?" : "Spots disponibles: ?";

    slide.appendChild(spotLabel);

    const grid = document.createElement("div");
    grid.classList.add("slot-grid");
    grid.id = `slot-grid-${areaId}`;
    slide.appendChild(grid);

    swiperWrapper.appendChild(slide);

    const parking_container = document.createElement("div");
    parking_container.classList.add("parking-container");
    parking_container.id = `parkingspace-${areaId}`;
    slide.appendChild(parking_container);
    swiperWrapper.appendChild(slide);

    for (let i = 0; i < 2; i++) {
      const parking_slots_holder = document.createElement("div");
      parking_slots_holder.classList.add("parking-slots-holder");
      parking_slots_holder.id = `holders-${areaId}-${i + 1}`;
      parking_container.appendChild(parking_slots_holder);
      if (i == 0) {
        const parking_way = document.createElement("div");
        parking_way.classList.add("parking-way");
        parking_way.id = `entry-way-${areaId}`;
        parking_container.appendChild(parking_way);
        const parking_way_2 = document.createElement("div");
        parking_way_2.classList.add("parking-way");
        parking_container.appendChild(parking_way_2);
      }
    }

    const wschema = window.location.protocol === "https:" ? "wss" : "ws";
    socket = initwebsocketconn(wschema, `ws/video/${areaId}/`);

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      const currentIndex = swiper.activeIndex;
      const activeAreaId = indexToAreaIdMap[currentIndex];
      if (data.area !== activeAreaId) return;
      areaLength = data.spot_details.length;
      const availableLabel = document.getElementById(`available-${data.area}`);
      if (availableLabel) {
        availableLabel.textContent =
          currentLanguage === "en"
            ? `Available spots : ${data.available_spots}`
            : `Spots disponibles: ${data.available_spots}`;
      }

      const slotGrid = document.getElementById(`slot-grid-${data.area}`);
      slotGrid.innerHTML = "";
      spotNameToIndexMap[areaId] = {};
      data.spot_details.forEach((spot, index) => {
        spotNameToIndexMap[areaId][spot.spot] = index;
        if (!spotNameToIndexMap[areaId].reverseMap) {
          spotNameToIndexMap[areaId].reverseMap = {};
        }
        spotNameToIndexMap[areaId].reverseMap[index] = spot.spot;
        const slotDiv = document.createElement("div");
        slotDiv.classList.add("slot");
        slotDiv.textContent = spot.spot;
        if (spot.status === "occupied") {
          slotDiv.classList.add("red");
        }
        slotGrid.appendChild(slotDiv);
      });
      const parking_slots_holder_target_1 = document.getElementById(
        `holders-${areaId}-1`
      );
      const parking_slots_holder_target_2 = document.getElementById(
        `holders-${areaId}-2`
      );
      for (let i = 0; i < areaLength; i++) {
        const parking_slots_verif = document.getElementById(
          `slot-${areaId}-${i}`
        );
        if (!parking_slots_verif) {
          const parking_slots = document.createElement("div");
          parking_slots.classList.add("parking-slot");
          parking_slots.id = `slot-${areaId}-${i}`;
          const p = document.createElement("p");
          const actualSpot = spotNameToIndexMap[areaId].reverseMap[i];
          p.textContent = actualSpot;
          parking_slots.appendChild(p);
          if (i < areaLength / 2 || areaLength < 6) {
            parking_slots_holder_target_1.appendChild(parking_slots);
            MaxareaTop = MaxareaTop + 1;
          } else {
            parking_slots_holder_target_2.appendChild(parking_slots);
          }
        }
      }
      let i = 0;
      if (data.spot_details) {
        data.spot_details.forEach((spot) => {
          let actualSpot = spotNameToIndexMap[areaId].reverseMap[i];
          let number = actualSpot?.match(/\d+/)?.[0];
          const slot = spotNameToIndexMap[areaId][spot.spot];
          i++;
          const isOccupied = spot.status === "occupied";
          w = document.getElementById(`parkingspace-${areaId}`).offsetWidth;
          h = document.getElementById(`parkingspace-${areaId}`).offsetHeight;
          if (isOccupied && !document.getElementById(`car-${areaId}-` + slot)) {
            carenter(areaId, slot, areaLength, number);
          } else if (
            !isOccupied &&
            document.getElementById(`car-${areaId}-` + slot)
          ) {
            carexit(areaId, slot, areaLength, number);
          }
        });
      }
    };
  });

  // swipeer effect initialization
  swiper = new Swiper(".swiper", {
    direction: "horizontal",
    loop: false,
    on: {
      slideChange: () => {
        items.forEach((el) => el.classList.remove("active"));
        const active = items[swiper.activeIndex];
        if (active) active.classList.add("active");
        const listItems = document.querySelectorAll("ul li");

        listItems.forEach((li) => {
          li.classList.remove("active");
        });
        listItems.forEach((li) => {
          if (parseInt(li.dataset.index) === swiper.activeIndex) {
            li.classList.add("active");
          }
        });
      },
    },
  });
});

// Function to handle car exit animation and removal
function carexit(areaId, slot, areaLength, actualSpot) {
  const slott = document.getElementById(`slot-${areaId}-${slot}`);
  const pElement = slott.querySelector("p");
  if (pElement) {
    pElement.textContent = actualSpot || `?`;
  }
  document.getElementById(`car-${areaId}-` + slot.toString()).style.position =
    "absolute";
  document.getElementById(
    `slot-${areaId}-` + slot.toString()
  ).style.background = "rgb(27,118,19)";
  if (slot < areaLength / 2 || areaLength < 6) {
    document.getElementById(
      `car-${areaId}-${slot}`
    ).style.animation = `car-exit-top-${areaId}-${slot} 2s both`;
  } else {
    document.getElementById(
      `car-${areaId}-${slot}`
    ).style.animation = `car-exit-bottom-${areaId}-${slot} 2s both`;
  }
  const car = document.getElementById(`car-${areaId}-${slot}`);
  car.addEventListener("animationend", function () {
    car.remove();
    const slott = document.getElementById(`slot-${areaId}-${slot}`);
    const pElement = slott.querySelector("p");
    if (pElement) {
      pElement.textContent = actualSpot || `?`;
    }
  });
}

// Function to generate a new car element and add it to the parking space
function generatenewcar(areaId, slot, areaLength) {
  const space = document.getElementById(`slot-${areaId}-${slot}`);
  const img = document.createElement("img");
  img.src = window.CAR_IMAGE_URL;
  img.className = "new-car-origin";
  img.id = `car-${areaId}-${slot}`;
  img.style.width = ((w * 0.14) / window.innerWidth) * 100 + "vw";
  const anim = document.createElement("style");
  img.style.right = "0%";
  let baseFactor = 777;
  let decrement = 91;

  if (slot < areaLength / 2 || areaLength < 6) {
    // Top-side slots

    const adjustedFactor = baseFactor - slot * decrement;

    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${areaId}-${slot} {
        from { 
          transform: rotate(270deg);
        } 
        80% {
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) 
        }
        90% {
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg);
        }
        to {
 transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg) translate(0px,-${
        h * 0.3
      }px);
        } 
      }`
    );

    anim.appendChild(rule);
    const exitAnim = document.createTextNode(`
      @-webkit-keyframes car-exit-top-${areaId}-${slot} {
        from { 
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg) translate(0px,-${
      h * 0.3
    }px);
        } 
        80% {
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg) translate(0px,-${
      h * 0.3
    }px) translateY(${h * 0.3}px) ;
        }
        90% {
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg) translate(0px,-${
      h * 0.3
    }px) translateY(${h * 0.3}px) rotate(90deg) ;
        }
        to {
          transform: rotate(270deg) translate(0px,-${adjustedFactor}%) rotate(90deg) translate(0px,-${
      h * 0.3
    }px) translateY(${
      h * 0.3
    }px) rotate(90deg)  translate(0px, -${adjustedFactor}%) ;
        }
      }
    `);
    anim.appendChild(exitAnim);
    img.addEventListener("animationend", function () {
      const pElement = space.querySelector("p");
      if (pElement) {
        pElement.textContent = "";
      }

      img.style.position = "relative";
      img.style.transform = `rotate(0deg)`;
      img.style.animation = "";
      img.style.transform = "translateY(-10%)";

      window.addEventListener("resize", () => {
        img.style.width = ((w * 0.15) / window.innerWidth) * 100 + "vw";
      });
    });
  } else {
    // Bottom-side slots
    const adjustedFactor =
      baseFactor - (slot - Math.ceil(areaLength / 2)) * decrement;
    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${areaId}-${slot} {
        from { 
          transform: rotate(-90deg);
        } 
        80% {
          transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) ;
        }
        90% {
          transform: rotate(-90deg) translate(0px,-${adjustedFactor}%)  rotate(-90deg);
        }
        to {
          transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) rotate(-90deg) translate(0px,-${
        h * 0.3
      }px);
        } 
      }`
    );
    anim.appendChild(rule);
    const exitAnim = document.createTextNode(
      `@-webkit-keyframes car-exit-bottom-${areaId}-${slot} {
        from { 
           transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) rotate(-90deg) translate(0px,-${
        h * 0.3
      }px);
        } 
        80% {
           transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) rotate(-90deg) translate(0px,-${
        h * 0.3
      }px) translate(0px,${h * 0.3}px);;
        }
        90% {
           transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) rotate(-90deg) translate(0px,-${
        h * 0.3
      }px) translate(0px,${h * 0.3}px) rotate(-90deg);
        }
        to {
           transform: rotate(-90deg) translate(0px,-${adjustedFactor}%) rotate(-90deg) translate(0px,-${
        h * 0.3
      }px) translate(0px,${
        h * 0.3
      }px) rotate(-90deg) translate(0px,-${adjustedFactor}%);
        } 
      }`
    );
    anim.appendChild(exitAnim);
    img.addEventListener("animationend", function () {
      const pElement = space.querySelector("p");
      if (pElement) {
        pElement.textContent = "";
      }

      img.style.position = "relative";
      img.style.transform = "rotate(180deg) translateY(15%)";
      img.style.animation = "";
      window.addEventListener("resize", () => {
        img.style.width = ((w * 0.15) / window.innerWidth) * 100 + "vw";
      });
    });

    document.head.appendChild(anim);
    space.appendChild(img);
  }
  document.head.appendChild(anim);
  space.appendChild(img);
}

// Function to handle car entry animation and creation
function carenter(areaId, slot, areaLength, actualSpot) {
  const carId = `car-${areaId}-${slot}`;
  if (!document.getElementById(carId)) {
    generatenewcar(areaId, slot, areaLength);
    const isTopRow = slot < areaLength / 2;
    const slotsPerRow = Math.ceil(areaLength / 2);

    document.getElementById(`slot-${areaId}-${slot}`).style.background =
      "rgb(146,18,18)";

    const carElement = document.getElementById(carId);
    if (!carElement) return;

    carElement.style.animation = `car-park-${areaId}-${slot} 2s both`;
  } else {
    carexit(areaId, slot, areaLength, actualSpot);
  }
}
