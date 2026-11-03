import { useCallback, useEffect, useState } from "react";
import { RotateCcw, Save } from "lucide-react";
import { fetchLayouts, fetchSnapshots, saveLayouts } from "../api.js";
import { useT } from "../../../shared/i18n.jsx";
import { lineColor, spotCode } from "../../../shared/zones/style.js";
import { useFeedback } from "../../../shared/ui/Feedback.jsx";
import "../styles/spots.css";

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

function nextName(spots) {
  const numbers = spots.map((s) => Number(String(s.name).match(/\d+/)?.[0] ?? 0));
  return `P${String(Math.max(0, ...numbers) + 1).padStart(2, "0")}`;
}

export default function SpotPicker() {
  const t = useT();
  const feedback = useFeedback();
  const [images, setImages] = useState(null);
  const [spots, setSpots] = useState({});
  const [pending, setPending] = useState(null);
  const [selected, setSelected] = useState(null);
  const [changes, setChanges] = useState(0);
  const [saving, setSaving] = useState(false);

  const loadCoordinates = useCallback(async () => {
    const res = await fetchLayouts();
    if (!res.ok) {
      return;
    }
    setSpots(
      Object.fromEntries(
        res.data.data.map(({ area, coordinates }) => [
          String(area),
          Object.entries(coordinates).map(([name, points]) => ({ name, points })),
        ])
      )
    );
    setPending(null);
    setSelected(null);
    setChanges(0);
  }, []);

  useEffect(() => {
    fetchSnapshots().then((res) => setImages(res.ok ? res.data.images : {}));
    loadCoordinates();
  }, [loadCoordinates]);

  const removeSpot = useCallback(
    (area, name) => {
      setSpots((current) => ({ ...current, [area]: current[area].filter((s) => s.name !== name) }));
      setSelected(null);
      setChanges((n) => n + 1);
      feedback.toast(t("Spot {code} removed.", { code: spotCode(area, name) }));
    },
    [feedback, t]
  );

  useEffect(() => {
    const onKey = (e) => {
      if ((e.key === "Delete" || e.key === "Backspace") && selected && e.target === document.body) {
        removeSpot(selected.area, selected.name);
      }
      if (e.key === "Escape") {
        setPending(null);
        setSelected(null);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected, removeSpot]);

  const addPoint = async (event, area) => {
    if (event.button !== 0) {
      return;
    }
    const box = event.currentTarget.getBoundingClientRect();
    const point = [event.clientX - box.left, event.clientY - box.top];
    setSelected(null);

    if (!pending || pending.area !== area) {
      setPending({ area, point });
      return;
    }

    const points = rectangleFrom(pending.point, point);
    setPending({ area, point: pending.point, end: point });
    const areaSpots = spots[area] ?? [];
    const name = await feedback.prompt({
      message: t("Name this spot"),
      defaultValue: nextName(areaSpots),
      confirmLabel: t("Add the spot"),
    });
    setPending(null);
    if (!name) {
      return;
    }
    if (!/^[\w -]{1,64}$/u.test(name) || areaSpots.some((s) => s.name === name)) {
      feedback.toast(t("Use a unique name made of letters, digits, spaces, - or _."), { error: true });
      return;
    }
    setSpots((current) => ({ ...current, [area]: [...(current[area] ?? []), { name, points }] }));
    setChanges((n) => n + 1);
  };

  const save = async () => {
    setSaving(true);
    const payload = Object.entries(spots).map(([area, areaSpots]) => ({
      area: String(area),
      coordinates: Object.fromEntries(areaSpots.map(({ name, points }) => [name, points.map((p) => p.map(Math.round))])),
    }));
    const res = await saveLayouts(payload);
    setSaving(false);
    feedback.toast(t(res.ok ? "Spots saved." : "The spots could not be saved."), { error: !res.ok });
    if (res.ok) {
      loadCoordinates();
    }
  };

  const areas = Object.keys(images ?? {}).sort((a, b) => a - b);

  return (
    <>
      <header className="page__head">
        <div>
          <h1 className="page__title">{t("Spots")}</h1>
          <p className="muted">
            {t("Click two opposite corners to draw a spot. Click a spot to select it, then press Delete or right-click to remove it.")}
          </p>
        </div>
      </header>

      {images === null ? (
        <span className="skeleton" style={{ height: 420 }} />
      ) : areas.length === 0 ? (
        <div className="panel empty">
          <b>{t("No camera image available")}</b>
          <p>{t("Add a camera whose stream responds, then come back to draw its spots.")}</p>
        </div>
      ) : (
        <div className="captures">
          {areas.map((area) => (
            <section className="capture panel" key={area} style={{ "--zone": lineColor(area) }}>
              <h2 className="capture__title heading">
                <span className="zone-dot" style={{ background: lineColor(area) }} aria-hidden="true" />
                Z{area} · {t("Zone {n}", { n: area })}
                <span className="caption">
                  {(spots[area] ?? []).length} {t("spots")}
                </span>
              </h2>
              <div
                className="capture__canvas"
                onMouseDown={(e) => addPoint(e, area)}
                onContextMenu={(e) => e.preventDefault()}
              >
                <img src={images[area]} alt={t("Camera image of zone {n}", { n: area })} draggable={false} />
                {pending?.area === area && (
                  <>
                    <span className="corner" style={{ left: pending.point[0], top: pending.point[1] }} />
                    {pending.end && <span className="drawing" style={bounds(rectangleFrom(pending.point, pending.end))} />}
                  </>
                )}
                {(spots[area] ?? []).map(({ name, points }) => {
                  const isSelected = selected?.area === area && selected?.name === name;
                  return (
                    <button
                      type="button"
                      key={name}
                      className={`spot-box ${isSelected ? "spot-box--selected" : ""}`}
                      style={bounds(points)}
                      onMouseDown={(e) => e.stopPropagation()}
                      onClick={() => setSelected(isSelected ? null : { area, name })}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        removeSpot(area, name);
                      }}
                    >
                      <span>{spotCode(area, name).split("-").pop()}</span>
                    </button>
                  );
                })}
              </div>
            </section>
          ))}
        </div>
      )}

      {changes > 0 && (
        <div className="savebar" role="region" aria-label={t("Unsaved changes")}>
          <p>
            <b className="num">{changes}</b> {t("unsaved change(s)")}
          </p>
          <button type="button" className="btn btn--secondary" onClick={loadCoordinates}>
            <RotateCcw size={16} aria-hidden="true" />
            {t("Undo changes")}
          </button>
          <button type="button" className="btn btn--primary" onClick={save} disabled={saving}>
            <Save size={16} aria-hidden="true" />
            {saving ? t("Saving…") : t("Save the spots")}
          </button>
        </div>
      )}
    </>
  );
}
