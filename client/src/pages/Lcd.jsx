import { useEffect, useState } from "react";
import css from "../styles/lcd.css?inline";
import { api, openSocket } from "../api.js";
import { useT } from "../i18n.jsx";

export default function Lcd() {
  const t = useT();
  const [areas, setAreas] = useState([]);
  const [area, setArea] = useState(null);
  const [emptySpots, setEmptySpots] = useState([]);

  useEffect(() => {
    api("/parking/areas/").then((res) => {
      if (res.ok && res.data.areas.length) {
        setAreas(res.data.areas);
        setArea(res.data.areas[0]);
      }
    });
  }, []);

  useEffect(() => {
    if (area === null) {
      return;
    }
    setEmptySpots([]);
    const socket = openSocket(`video/${area}/`);
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setEmptySpots(data.spot_details.filter((s) => s.status === "empty").map((s) => s.spot));
    };
    return () => socket.close();
  }, [area]);

  return (
    <>
      <style>{css}</style>
      <div className="container">
        <h1>
          {t("Area")} : {area}
        </h1>

        <label htmlFor="areaSelect">{t("Choose an area")} :</label>
        <select id="areaSelect" value={area ?? ""} onChange={(e) => setArea(Number(e.target.value))}>
          {areas.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>

        <div className="status">
          <h2>
            {t("Available spots")} : <span>{emptySpots.length}</span>
          </h2>
          <ul>
            {emptySpots.map((spot) => {
              const number = Number(spot.match(/\d+/)?.[0] ?? 0);
              return (
                <li key={spot}>
                  {spot} <span className="arrow">{number % 2 === 0 ? "→" : "←"}</span>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </>
  );
}
