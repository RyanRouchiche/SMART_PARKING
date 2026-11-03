import { Link, Navigate, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight } from "lucide-react";
import { useT } from "../../../shared/i18n.jsx";
import { useZone } from "../ZonesProvider.jsx";
import "../styles/lcd.css";

function spotNumber(code) {
  return Number(code.match(/(\d+)$/)?.[1] ?? 0);
}

export default function Lcd() {
  const t = useT();
  const navigate = useNavigate();
  const { area } = useParams();
  const { zone, zones } = useZone(area);

  if (!zones) {
    return <div className="lcd" />;
  }
  if (!area || !zone) {
    return zones.length ? <Navigate to={`/lcd/${zones[0].area}`} replace /> : <Navigate to="/" replace />;
  }

  const free = zone.spots.filter((s) => s.status === "empty");
  const left = free.filter((s) => spotNumber(s.code) % 2 === 1);
  const right = free.filter((s) => spotNumber(s.code) % 2 === 0);
  const unavailable = zone.state === "offline" || zone.state === "stale" || zone.state === "connecting";

  let headline;
  if (unavailable) {
    headline = <p className="lcd__word lcd__word--alert">{t("OUT OF SERVICE")}</p>;
  } else if (zone.state === "full") {
    headline = <p className="lcd__word lcd__word--alert">{t("FULL")}</p>;
  } else {
    headline = (
      <>
        <p key={zone.free} className="lcd__count num">
          {zone.free}
        </p>
        <p className="lcd__unit">{t(zone.free === 1 ? "free spot" : "free spots")}</p>
      </>
    );
  }

  return (
    <div className="lcd" style={{ "--zone": zone.color }}>
      <header className="lcd__head">
        <h1>
          <span className="lcd__dot" aria-hidden="true" />
          {zone.code} · {t("Zone {n}", { n: zone.area })}
        </h1>
        <div className="lcd__controls">
          <select aria-label={t("Choose a zone")} value={zone.area} onChange={(e) => navigate(`/lcd/${e.target.value}`)}>
            {zones.map((z) => (
              <option key={z.area} value={z.area}>
                {z.code}
              </option>
            ))}
          </select>
          <Link to="/">{t("Exit")}</Link>
        </div>
      </header>

      <main className="lcd__main" aria-live="polite">
        {headline}
      </main>

      {!unavailable && free.length > 0 && (
        <footer className="lcd__spots">
          {left.length > 0 && (
            <p>
              <ArrowLeft size={56} strokeWidth={2.5} aria-label={t("Left")} />
              <span className="num">{left.map((s) => s.code.split("-").pop()).join("  ")}</span>
            </p>
          )}
          {right.length > 0 && (
            <p>
              <span className="num">{right.map((s) => s.code.split("-").pop()).join("  ")}</span>
              <ArrowRight size={56} strokeWidth={2.5} aria-label={t("Right")} />
            </p>
          )}
        </footer>
      )}
    </div>
  );
}
