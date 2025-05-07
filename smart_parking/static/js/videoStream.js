let swiper;
import {scheduleStaticTokenRefresh} from './utils.js';

document.addEventListener("DOMContentLoaded", async () => {
  scheduleStaticTokenRefresh();
  const res = await fetch("/parking/areas/");
  const areas = await res.json();

  const areaList = document.getElementById("area-list");
  const swiperWrapper = document.getElementById("swiper-wrapper");

  areas.forEach((areaId, index) => {
    const li = document.createElement("li");
    li.textContent = `Area ${areaId}`;
    li.dataset.index = index;
    if (index === 0) li.classList.add("active");

    li.addEventListener("click", () => {
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

    const wschema = window.location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${wschema}://${window.location.host}/ws/video/${areaId}/`);

    socket.onmessage = function (event) {
      const data = JSON.parse(event.data);

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
    };
  });

  swiper = new Swiper(".swiper", {
    direction: "horizontal",
    loop: false,
    on: {
      slideChange: () => {
        const items = document.querySelectorAll("#area-list li");
        items.forEach((el) => el.classList.remove("active"));
        const active = items[swiper.activeIndex];
        if (active) active.classList.add("active");
      }
    }
  });
});
