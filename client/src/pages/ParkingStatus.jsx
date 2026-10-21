import { useEffect, useRef, useState } from "react";
import { Swiper, SwiperSlide } from "swiper/react";
import css from "../styles/stream.css?inline";
import Navbar from "../components/Navbar.jsx";
import { api, openSocket } from "../api.js";
import { useT } from "../i18n.jsx";
import carImage from "../assets/car.png";

const BASE_FACTOR = 777;
const FACTOR_STEP = 91;

function isTopRow(slot, count) {
  return slot < count / 2 || count < 6;
}

function keyframes(areaId, slot, count, height) {
  const top = isTopRow(slot, count);
  const turn = top ? "270deg" : "-90deg";
  const spin = top ? "90deg" : "-90deg";
  const factor = BASE_FACTOR - (top ? slot : slot - Math.ceil(count / 2)) * FACTOR_STEP;
  const lift = height * 0.3;
  const parked = `rotate(${turn}) translate(0px,-${factor}%) rotate(${spin}) translate(0px,-${lift}px)`;
  const exitName = `car-exit-${top ? "top" : "bottom"}-${areaId}-${slot}`;

  return `
    @keyframes car-park-${areaId}-${slot} {
      from { transform: rotate(${turn}); }
      80% { transform: rotate(${turn}) translate(0px,-${factor}%); }
      90% { transform: rotate(${turn}) translate(0px,-${factor}%) rotate(${spin}); }
      to { transform: ${parked}; }
    }
    @keyframes ${exitName} {
      from { transform: ${parked}; }
      80% { transform: ${parked} translateY(${lift}px); }
      90% { transform: ${parked} translateY(${lift}px) rotate(${spin}); }
      to { transform: ${parked} translateY(${lift}px) rotate(${spin}) translate(0px,-${factor}%); }
    }`;
}

function Car({ areaId, slot, count, phase, width, onAnimationEnd }) {
  const top = isTopRow(slot, count);
  const style = { right: "0%", width: `${width * (phase === "parked" ? 0.15 : 0.14)}px` };

  if (phase === "parking") {
    style.animation = `car-park-${areaId}-${slot} 2s both`;
  } else if (phase === "leaving") {
    style.animation = `car-exit-${top ? "top" : "bottom"}-${areaId}-${slot} 2s both`;
  } else {
    style.position = "relative";
    style.transform = top ? "translateY(-10%)" : "rotate(180deg) translateY(15%)";
  }

  return <img src={carImage} className="new-car-origin" style={style} onAnimationEnd={onAnimationEnd} />;
}

function AreaSlide({ areaId }) {
  const t = useT();
  const containerRef = useRef(null);
  const [spots, setSpots] = useState([]);
  const [available, setAvailable] = useState(null);
  const [cars, setCars] = useState({});
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const observer = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height })
    );
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    const socket = openSocket(`video/${areaId}/`);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setSpots(data.spot_details);
      setAvailable(data.available_spots);
      setCars((current) => {
        const next = { ...current };
        data.spot_details.forEach(({ status }, slot) => {
          const occupied = status === "occupied";
          if (occupied && !next[slot]) {
            next[slot] = "parking";
          } else if (!occupied && next[slot] && next[slot] !== "leaving") {
            next[slot] = "leaving";
          }
        });
        return next;
      });
    };
    return () => socket.close();
  }, [areaId]);

  const onCarAnimationEnd = (slot) =>
    setCars((current) => {
      const next = { ...current };
      if (next[slot] === "leaving") {
        delete next[slot];
      } else {
        next[slot] = "parked";
      }
      return next;
    });

  const count = spots.length;
  const renderSlot = (spot, slot) => (
    <div
      className="parking-slot"
      key={spot.spot}
      style={cars[slot] && cars[slot] !== "leaving" ? { background: "rgb(146,18,18)" } : undefined}
    >
      <p>{cars[slot] === "parked" ? "" : spot.spot}</p>
      {cars[slot] && (
        <Car
          areaId={areaId}
          slot={slot}
          count={count}
          phase={cars[slot]}
          width={size.width}
          onAnimationEnd={() => onCarAnimationEnd(slot)}
        />
      )}
    </div>
  );

  return (
    <>
      <style>{spots.map((_, slot) => keyframes(areaId, slot, count, size.height)).join("")}</style>
      <div className="area-title">
        {t("Area")} {areaId}
      </div>
      <div className="available-spots">
        {t("Available spots")} : {available ?? "?"}
      </div>
      <div className="slot-grid">
        {spots.map((spot) => (
          <div className={`slot ${spot.status === "occupied" ? "red" : ""}`} key={spot.spot}>
            {spot.spot}
          </div>
        ))}
      </div>
      <div className="parking-container" ref={containerRef}>
        <div className="parking-slots-holder">
          {spots.map((spot, slot) => isTopRow(slot, count) && renderSlot(spot, slot))}
        </div>
        <div className="parking-way" />
        <div className="parking-way" />
        <div className="parking-slots-holder">
          {spots.map((spot, slot) => !isTopRow(slot, count) && renderSlot(spot, slot))}
        </div>
      </div>
    </>
  );
}

export default function ParkingStatus() {
  const t = useT();
  const [areas, setAreas] = useState([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [swiper, setSwiper] = useState(null);

  useEffect(() => {
    api("/parking/areas/").then((res) => res.ok && setAreas(res.data.areas));
  }, []);

  return (
    <>
      <style>{css}</style>
      <Navbar />

      <div className="layout">
        <div className={`sidebar ${sidebarOpen ? "" : "close"}`}>
          <button id="open" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <span>{sidebarOpen ? ">>" : "<<"}</span>
          </button>
          <h2>{t("Areas")}</h2>
          <ul>
            {areas.map((areaId, index) => (
              <li
                key={areaId}
                className={index === activeIndex ? "active" : ""}
                onClick={() => swiper?.slideTo(index)}
              >
                {t("Area")} {areaId}
              </li>
            ))}
          </ul>
        </div>
        <Swiper onSwiper={setSwiper} onSlideChange={(s) => setActiveIndex(s.activeIndex)}>
          {areas.map((areaId) => (
            <SwiperSlide key={areaId}>
              <AreaSlide areaId={areaId} />
            </SwiperSlide>
          ))}
        </Swiper>
      </div>
    </>
  );
}
