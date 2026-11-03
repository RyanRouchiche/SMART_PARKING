import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { useT } from "../i18n.jsx";
import { useZones } from "../zones.jsx";
import { StateChip, isAlert, useAgo } from "../components/ZoneStatus.jsx";
import "../styles/network.css";

const STATIONS_PER_LINE = 4;

function chunk(list, size) {
  return Array.from({ length: Math.ceil(list.length / size) }, (_, i) => list.slice(i * size, i * size + size));
}

function Station({ zone, onOpen }) {
  const t = useT();
  const fill = zone.total && zone.free !== null ? Math.round(((zone.total - zone.free) / zone.total) * 100) : 0;
  const count = zone.free === null ? "—" : zone.free;
  const caption = zone.state === "full" ? t("Full") : zone.state === "offline" ? t("Offline") : t("Zone {n}", { n: zone.area });

  return (
    <button
      type="button"
      className={`station station--${zone.state}`}
      style={{ "--zone": zone.color, "--fill": `${fill}%` }}
      onClick={() => onOpen(zone.area)}
      aria-label={t("Open zone {code}: {count} free spots", { code: zone.code, count })}
    >
      <span className={`station__marker ${zone.dashed ? "station__marker--dashed" : ""}`} aria-hidden="true">
        <span className="station__fill" />
      </span>
      <span className="station__label">
        <b className="num">
          {zone.code} · {count}
        </b>
        <span className="caption">{caption}</span>
      </span>
    </button>
  );
}

const LEGEND = [
  { label: "Free", fill: "0%" },
  { label: "Filling up", fill: "60%" },
  { label: "Full", fill: "100%" },
  { label: "Offline", offline: true },
];

function Schema({ zones, onOpen }) {
  const t = useT();
  return (
    <div className={`schema panel ${zones.length <= 2 ? "schema--large" : ""}`}>
      {chunk(zones, STATIONS_PER_LINE).map((line, index) => (
        <div className="schema__line" key={index}>
          {line.map((zone) => (
            <div className="schema__stop" key={zone.area}>
              <span className="schema__track" style={{ background: zone.color }} />
              <Station zone={zone} onOpen={onOpen} />
            </div>
          ))}
          <span className="schema__track schema__track--end" style={{ background: line[line.length - 1].color }} />
        </div>
      ))}
      <ul className="schema__legend caption">
        {LEGEND.map(({ label, fill, offline }) => (
          <li key={label}>
            <span
              className={`legend-marker ${offline ? "legend-marker--offline" : ""}`}
              style={{ "--fill": fill }}
              aria-hidden="true"
            />
            {t(label)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function StatusBoard({ zones, now, onOpen }) {
  const t = useT();
  const ago = useAgo();
  const sorted = [...zones].sort((a, b) => Number(isAlert(b.state)) - Number(isAlert(a.state)) || a.area - b.area);
  const alerts = zones.filter((z) => isAlert(z.state)).length;

  return (
    <aside className="board" aria-labelledby="board-title">
      <div>
        <h2 id="board-title" className="heading">
          {t("Line status")}
        </h2>
        <p className={alerts ? "board__summary board__summary--alert" : "board__summary muted"}>
          {alerts ? t("{n} zone(s) need attention", { n: alerts }) : t("All cameras are working")}
        </p>
      </div>
      <ul className="board__rows">
        {sorted.map((zone) => (
          <li key={zone.area}>
            <button
              type="button"
              className={`status-row ${isAlert(zone.state) ? "status-row--alert" : ""}`}
              onClick={() => onOpen(zone.area)}
            >
              <span className="zone-dot" style={{ background: zone.color }} aria-hidden="true" />
              <span className="status-row__body">
                <b>
                  {zone.code} · {t("Zone {n}", { n: zone.area })}
                </b>
                <span className="caption">
                  {zone.total} {t("spots")} · {ago(zone.updatedAt, now)}
                </span>
                <StateChip state={zone.state} />
              </span>
              <span className="status-row__count num">{zone.free === null ? "—" : zone.free}</span>
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}

export default function Network() {
  const t = useT();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { zones, now } = useZones();
  const open = (area) => navigate(`/zones/${area}`);

  if (!zones) {
    return (
      <div className="network">
        <span className="skeleton" style={{ width: 240, height: 28 }} />
        <span className="skeleton" style={{ height: 360 }} />
      </div>
    );
  }

  const known = zones.filter((z) => z.free !== null);
  const free = known.reduce((sum, z) => sum + z.free, 0);
  const total = zones.reduce((sum, z) => sum + z.total, 0);

  return (
    <>
      <header className="page__head">
        <div>
          <h1 className="page__title">{t("Zone network")}</h1>
          <p className="muted">{t("Live, updated every 5 seconds")}</p>
        </div>
        {zones.length > 0 && (
          <p className="total">
            <strong className="num">{free}</strong>
            <span>{t("free spots out of {n}", { n: total })}</span>
          </p>
        )}
      </header>

      {zones.length === 0 ? (
        <div className="panel empty">
          <b>{t("No zone yet")}</b>
          <p>{t("Add a camera, then draw its spots to create the first zone.")}</p>
          {user.role === "admin" && (
            <Link to="/cameras" className="btn btn--primary" style={{ marginTop: 16 }}>
              {t("Add a camera")}
            </Link>
          )}
        </div>
      ) : (
        <div className="network">
          <Schema zones={zones} onOpen={open} />
          <StatusBoard zones={zones} now={now} onOpen={open} />
        </div>
      )}
    </>
  );
}
