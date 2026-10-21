import { useCallback, useEffect, useState } from "react";
import css from "../styles/pick_up_spot.css?inline";
import Navbar from "../components/Navbar.jsx";
import { useModal } from "../components/Modal.jsx";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";

function rectangleFrom([x1, y1], [x2, y2]) {
  const [left, right] = [Math.min(x1, x2), Math.max(x1, x2)];
  const [top, bottom] = [Math.min(y1, y2), Math.max(y1, y2)];
  return [[left, top], [right, top], [right, bottom], [left, bottom]];
}

function bounds(points) {
  const xs = points.map((p) => p[0]);
  const ys = points.map((p) => p[1]);
  const left = Math.min(...xs);
  const top = Math.min(...ys);
  return { left, top, width: Math.max(...xs) - left, height: Math.max(...ys) - top };
}

function uniqueSpotName(spots) {
  let counter = 1;
  while (spots.some((s) => s.name === `Spot ${counter}`)) counter++;
  return `Spot ${counter}`;
}

export default function SpotPicker() {
  const t = useT();
  const modal = useModal();
  const [images, setImages] = useState({});
  const [spots, setSpots] = useState({});
  const [pending, setPending] = useState(null);
  const [dirty, setDirty] = useState(false);

  const loadCoordinates = useCallback(async () => {
    const res = await api("/parking/coordinates/");
    if (!res.ok) {
      return;
    }
    setSpots(
      Object.fromEntries(
        res.data.data.map(({ area, coordinates }) => [
          area,
          Object.entries(coordinates).map(([name, points]) => ({ name, points })),
        ])
      )
    );
    setPending(null);
    setDirty(false);
  }, []);

  useEffect(() => {
    api("/parking/snapshots/").then((res) => {
      if (res.status === 403) {
        modal.notify(t("Only admin"));
      } else if (res.ok) {
        setImages(res.data.images);
      }
    });
    loadCoordinates();
  }, [loadCoordinates]);

  const addPoint = async (event, area) => {
    if (event.button !== 0) {
      return;
    }
    const box = event.currentTarget.getBoundingClientRect();
    const point = [event.clientX - box.left, event.clientY - box.top];

    if (!pending || pending.area !== area) {
      setPending({ area, point });
      return;
    }

    setPending(null);
    const points = rectangleFrom(pending.point, point);
    const areaSpots = spots[area] ?? [];
    const name = (await modal.prompt(t("Pick a name for the spot (e.g., Spot 1)"))) || uniqueSpotName(areaSpots);

    setSpots((current) => ({ ...current, [area]: [...(current[area] ?? []), { name, points }] }));
    setDirty(true);
    modal.notify(t("Spot selected: {spot} in area {area}.", { spot: name, area }));
  };

  const removeSpot = (event, area, name) => {
    event.preventDefault();
    setSpots((current) => ({ ...current, [area]: current[area].filter((s) => s.name !== name) }));
    setDirty(true);
    modal.notify(t('Spot "{spot}" deleted.', { spot: name }));
  };

  const save = async () => {
    const payload = Object.entries(spots).map(([area, areaSpots]) => ({
      area: String(area),
      coordinates: Object.fromEntries(
        areaSpots.map(({ name, points }) => [name, points.map((p) => p.map(Math.round))])
      ),
    }));
    const res = await api("/parking/coordinates/", { method: "POST", body: payload });
    modal.notify(t(res.ok ? "Coordinates saved successfully!" : "Error saving coordinates."));
    loadCoordinates();
  };

  return (
    <>
      <style>{css}</style>
      <Navbar />

      <div className="main">
        <div className="main__container">
          <div className="main__content">
            <h1>{t("Pick a parking spot")}</h1>
            <div className="area-container">
              {Object.entries(images).map(([area, src]) => (
                <div
                  className="image-container"
                  key={area}
                  onMouseDown={(e) => addPoint(e, area)}
                  onContextMenu={(e) => e.preventDefault()}
                >
                  <h2>
                    {t("Area")} {area}
                  </h2>
                  <img src={src} alt={`Camera in area ${area}`} draggable={false} />

                  {pending?.area === area && (
                    <div className="selected-point" style={{ left: pending.point[0], top: pending.point[1] }} />
                  )}

                  {(spots[area] ?? []).map(({ name, points }) => (
                    <div key={name}>
                      {points.map(([x, y], i) => (
                        <div className="selected-point" key={i} style={{ left: x, top: y }} />
                      ))}
                      <div
                        className="spot-rectangle context-menu-enabled"
                        style={bounds(points)}
                        onContextMenu={(e) => removeSpot(e, area, name)}
                      >
                        <span>{name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div className="bottom__area">
              <button className={`save-button ${dirty ? "active" : ""}`} id="Undo" onClick={loadCoordinates}>
                {t("Undo Changes")}
              </button>
              <button className="save-button" onClick={save}>
                {t("Save Changes")}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
