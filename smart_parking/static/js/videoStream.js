import { scheduleStaticTokenRefresh } from "./utils.js";
let swiper, w, h;
let areaLength;
const indexToAreaIdMap = {};

//calls
const areaList = document.getElementById("area-list");
const swiperWrapper = document.getElementById("swiper-wrapper");
const items = document.querySelectorAll("#area-list li");
const sidebar = document.getElementById("sidebar");
const open = document.getElementById("open");

open.addEventListener("click", () => {
  sidebar.classList.toggle("close");
});

// Function to handle token refresh +  dynamic div creation based on websocket data
document.addEventListener("DOMContentLoaded", async () => {
  const menu = document.querySelector("#mobile-menu");
  const menuLinks = document.querySelector(".navbar__menu");

  menu.addEventListener("click", function () {
    menu.classList.toggle("is-active");
    menuLinks.classList.toggle("active");
  });

  scheduleStaticTokenRefresh();
  const res = await fetch("/parking/areas/");
  const areas = await res.json();

  areas.forEach((areaId, index) => {
    indexToAreaIdMap[index] = areaId;
    const li = document.createElement("li");
    li.textContent = `Area ${areaId}`;
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
    title.textContent = `Area ${areaId}`;
    slide.appendChild(title);

    const spotLabel = document.createElement("div");
    spotLabel.classList.add("available-spots");
    spotLabel.id = `available-${areaId}`;
    spotLabel.textContent = "Spots disponibles: ?";
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
    }

    const wschema = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(
      `${wschema}://${window.location.host}/ws/video/${areaId}/`
    );

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);
      const currentIndex = swiper.activeIndex;
      const activeAreaId = indexToAreaIdMap[currentIndex];
      if (data.area !== activeAreaId) return;
      areaLength = data.spot_details.length;
      const availableLabel = document.getElementById(`available-${data.area}`);
      if (availableLabel) {
        availableLabel.textContent = `Spots disponibles: ${data.available_spots}`;
      }

      const slotGrid = document.getElementById(`slot-grid-${data.area}`);
      slotGrid.innerHTML = "";
      data.spot_details.forEach((spot) => {
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
          p.textContent = `${i + 1}`;
          parking_slots.appendChild(p);
          // parking_slots.textContent = `${i + 1}`;
          if (i < areaLength / 2) {
            parking_slots_holder_target_1.appendChild(parking_slots);
          } else {
            parking_slots_holder_target_2.appendChild(parking_slots);
          }
        }
      }
      w = document.getElementById(`parkingspace-${areaId}`).offsetWidth;
      h = document.getElementById(`parkingspace-${areaId}`).offsetHeight;
      if (data.spot_details) {
        data.spot_details.forEach((spot) => {
          let number = spot.spot.match(/\d+/)[0] - 1;
          const slot = parseInt(number);
          const isOccupied = spot.status === "occupied";

          if (isOccupied && !document.getElementById(`car-${areaId}-` + slot)) {
            carenter(areaId, slot, areaLength);
          } else if (
            !isOccupied &&
            document.getElementById(`car-${areaId}-` + slot)
          ) {
            carexit(areaId, slot, areaLength);
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
      },
    },
  });
});

// Function to handle car exit animation and removal
function carexit(areaId, slot, areaLength) {
  const slott = document.getElementById(`slot-${areaId}-${slot}`);
  const pElement = slott.querySelector("p");
  if (pElement) {
    pElement.textContent = ""; // Set the text content of the <p> element to nothing
  }
  document.getElementById(`car-${areaId}-` + slot.toString()).style.position =
    "absolute";
  document.getElementById(
    `slot-${areaId}-` + slot.toString()
  ).style.background = "rgb(27,118,19)";
  if (slot < areaLength / 2) {
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
  });
}

// Function to generate a new car element and add it to the parking space
function generatenewcar(areaId, slot, areaLength) {
  const space = document.getElementById(`slot-${areaId}-${slot}`);
  const img = document.createElement("img");
  img.src = window.CAR_IMAGE_URL;
  img.className = "new-car-origin";
  img.id = `car-${areaId}-${slot}`;
  img.style.width = ((w * 0.2) / window.innerWidth) * 100 + "vw";
  const anim = document.createElement("style");
  let totalOffset, verticalOffset;
  let rotation = "90deg";

  if (slot < areaLength / 2) {
    // Left-side slots (0–4)
    img.style.left = "12%";

    // if (slot == areaLength / 2 - 1) {
    //   verticalOffset += h * 0.0012;
    //
    const screenSizes = [
      { maxWidth: 600, totalOffset: "7vh", verticalOffsetFactor: 0.83 },
      { maxWidth: 800, totalOffset: "9.4vh", verticalOffsetFactor: 0.809 },
      { maxWidth: 1000, totalOffset: "13vh", verticalOffsetFactor: 0.8 },
      { maxWidth: 1100, totalOffset: "16vh", verticalOffsetFactor: 0.77 },
      { maxWidth: 1300, totalOffset: "18vh", verticalOffsetFactor: 0.77 },
      { maxWidth: 1500, totalOffset: "22vh", verticalOffsetFactor: 0.75 },
      { maxWidth: 1700, totalOffset: "25vh", verticalOffsetFactor: 0.73 },
    ];

    for (let size of screenSizes) {
      if (window.matchMedia(`(max-width: ${size.maxWidth}px)`).matches) {
        totalOffset = size.totalOffset;
        verticalOffset =
          h * (size.verticalOffsetFactor + 0.11 * (slot * (areaLength / 2)));
        break;
      }
    }

    if (!totalOffset) {
      totalOffset = "30vh";
      verticalOffset = h * (0.73 + 0.11 * (slot * (areaLength / 2)));
    }

    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${areaId}-${slot} {
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
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -${totalOffset});
        }
      }`
    );

    anim.appendChild(rule);
    const exitAnim = document.createTextNode(`
      @-webkit-keyframes car-exit-top-${areaId}-${slot} {
        from{
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -${totalOffset});
        }
        60% {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -${totalOffset}) translate(0, 110%); ;
        }
        80% {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -${totalOffset}) translate(0, 110%) rotate(${rotation});
        }
        to {
          transform: translate(0, -${verticalOffset}px) rotate(${rotation}) translate(0, -${totalOffset}) translate(0, 110%) rotate(${rotation}) translate(0, -${
      verticalOffset * 2
    }px);
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
      img.style.transform = `rotate(90deg)`;
      img.style.right = "0";
      img.style.animation = "";

      window.addEventListener("resize", () => {
        img.style.width = ((w * 0.2) / window.innerWidth) * 100 + "vw";
      });
    });
  } else {
    // Right-side slots (5–9)

    img.style.right = "12%";
    const screenSizes = [
      { maxWidth: 600, totalOffset: "8vh", verticalOffsetFactor: 0.72 },
      { maxWidth: 800, totalOffset: "10.6vh", verticalOffsetFactor: 0.7 },
      { maxWidth: 1000, totalOffset: "15vh", verticalOffsetFactor: 0.69 },
      { maxWidth: 1100, totalOffset: "18vh", verticalOffsetFactor: 0.66 },
      { maxWidth: 1300, totalOffset: "20vh", verticalOffsetFactor: 0.66 },
      { maxWidth: 1500, totalOffset: "25vh", verticalOffsetFactor: 0.64 },
      { maxWidth: 1700, totalOffset: "28vh", verticalOffsetFactor: 0.62 },
    ];

    for (let size of screenSizes) {
      if (window.matchMedia(`(max-width: ${size.maxWidth}px)`).matches) {
        totalOffset = size.totalOffset;
        verticalOffset =
          h * (size.verticalOffsetFactor + 0.11 * (slot * (areaLength / 2)));
        break;
      }
    }

    if (!totalOffset) {
      totalOffset = "33vh";
      verticalOffset = h * (0.62 + 0.11 * (slot * (areaLength / 2)));
    }
    // if (slot == areaLength - 1) {
    //   verticalOffset += h * 0.0012;
    // }
    const rule = document.createTextNode(
      `@-webkit-keyframes car-park-${areaId}-${slot} {
        0% { transform: translateY(0) rotate(0deg); }
        70% { transform: translateY(-${verticalOffset}px) rotate(0deg); }
        80% { transform: translateY(-${verticalOffset}px) rotate(-90deg); }
        100% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-${totalOffset});}
      }`
    );
    anim.appendChild(rule);
    const exitAnim = document.createTextNode(
      `@-webkit-keyframes car-exit-bottom-${areaId}-${slot} {
        0% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-${totalOffset}); }
        60% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-${totalOffset}) translateY(110%);}
        80% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-${totalOffset})  translateY(110%) rotate(-${rotation}); }
        100% { transform: translateY(-${verticalOffset}px) rotate(-90deg) translateY(-${totalOffset}) translateY(110%) rotate(-${rotation}) translateY(-${
        verticalOffset * 2
      }px);}
      }`
    );
    anim.appendChild(exitAnim);
    img.addEventListener("animationend", function () {
      const pElement = space.querySelector("p");
      if (pElement) {
        pElement.textContent = "";
      }

      img.style.position = "relative";
      img.style.transform = `translateX(-80%) rotate(-90deg)`;
      img.style.animation = "";

      // Only adjust the width on resize, not position
      window.addEventListener("resize", () => {
        img.style.width = ((w * 0.2) / window.innerWidth) * 100 + "vw";
      });
    });

    document.head.appendChild(anim);
    space.appendChild(img);
  }
  document.head.appendChild(anim);
  space.appendChild(img);
}

// Function to handle car entry animation and creation
function carenter(areaId, slot, areaLength) {
  if (!document.getElementById(`car-${areaId}-` + slot.toString())) {
    generatenewcar(areaId, slot, areaLength);
    document.getElementById(
      `slot-${areaId}-` + slot.toString()
    ).style.background = "rgb(146,18,18)";
    if (slot != areaLength / 2 && slot != areaLength)
      document.getElementById(`car-${areaId}-${slot}`).style.right =
        -w +
        w * 0.04 +
        (5 - ((slot + 1) % 5)) * (w * 0.8 * 0.2) +
        w * 0.8 * 0.05 +
        "px";
    else
      document.getElementById(`car-${areaId}-${slot}`).style.right =
        -w + w * 0.04 + w * 0.8 * 0.05 + "px";
    if (slot < areaLength)
      document.getElementById(
        `car-${areaId}-${slot}`
      ).style.animation = `car-park-${areaId}-${slot} 2s both`;
    else
      document.getElementById(
        `car-${areaId}-${slot}`
      ).style.animation = `car-park-${areaId}-${slot} 2s both`;
  } else {
    carexit(areaId, slot, areaLength);
  }
}
