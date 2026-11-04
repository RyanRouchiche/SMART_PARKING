import { useEffect, useRef, useState } from "react";
import { Link, Navigate, NavLink, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { useT } from "../../../shared/i18n.jsx";
import { useZone } from "../ZonesProvider.jsx";
import { StateChip, useAgo } from "../components/ZoneStatus.jsx";
import carImage from "../assets/car.png";
import "../styles/zone.css";

const BASE_FACTOR = 777;
const FACTOR_STEP = 91;
const DRIVE_MS = 1200;
const STAGGER_MS = 60;

function isTopRow(slot, count) {
  return slot < count / 2 || count < 6;
}

function keyframes(area, slot, count, height) {
  const top = isTopRow(slot, count);
  const turn = top ? "270deg" : "-90deg";
  const spin = top ? "90deg" : "-90deg";
  const factor = BASE_FACTOR - (top ? slot : slot - Math.ceil(count / 2)) * FACTOR_STEP;
  const lift = height * 0.3;
  const parked = `rotate(${turn}) translate(0px,-${factor}%) rotate(${spin}) translate(0px,-${lift}px)`;

  return `
    @keyframes park-${area}-${slot} {
      from { transform: rotate(${turn}); opacity: 0; }
      8% { opacity: 1; }
      80% { transform: rotate(${turn}) translate(0px,-${factor}%); }
      90% { transform: rotate(${turn}) translate(0px,-${factor}%) rotate(${spin}); }
      to { transform: ${parked}; opacity: 1; }
    }
    @keyframes leave-${area}-${slot} {
      from { transform: ${parked}; }
      80% { transform: ${parked} translateY(${lift}px); }
      90% { transform: ${parked} translateY(${lift}px) rotate(${spin}); opacity: 1; }
      to { transform: ${parked} translateY(${lift}px) rotate(${spin}) translate(0px,-${factor}%); opacity: 0; }
    }`;
}

function Car({ area, slot, count, car, width, onDone }) {
  const top = isTopRow(slot, count);
  const style = { right: 0, width: `${width * (car.phase === "parked" ? 0.15 : 0.14)}px` };

  if (car.phase === "parking") {
    style.animation = `park-${area}-${slot} ${DRIVE_MS}ms ${car.delay}ms both`;
  } else if (car.phase === "leaving") {
    style.animation = `leave-${area}-${slot} ${DRIVE_MS}ms both`;
  } else {
    style.position = "relative";
    style.transform = top ? "translateY(-10%)" : "rotate(180deg) translateY(15%)";
  }

  return <img src={carImage} alt="" className="car" style={style} onAnimationEnd={onDone} />;
}

function useCars(zone) {
  const [cars, setCars] = useState({});
  const replayed = useRef(false);

  useEffect(() => {
    if (!zone || zone.free === null) {
      return;
    }
    setCars((current) => {
      const next = { ...current };
      let order = 0;
      zone.spots.forEach(({ status }, slot) => {
        const occupied = status === "occupied";
        if (occupied && !next[slot]) {
          next[slot] = { phase: "parking", delay: replayed.current ? 0 : order++ * STAGGER_MS };
        } else if (!occupied && next[slot] && next[slot].phase !== "leaving") {
          next[slot] = { phase: "leaving", delay: 0 };
        }
      });
      replayed.current = true;
      return next;
    });
  }, [zone]);

  const settle = (slot) =>
    setCars((current) => {
      const next = { ...current };
      if (next[slot]?.phase === "leaving") {
        delete next[slot];
      } else if (next[slot]) {
        next[slot] = { phase: "parked", delay: 0 };
      }
      return next;
    });

  return [cars, settle];
}

function useSize(ref) {
  const [size, setSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    const observer = new ResizeObserver(([entry]) =>
      setSize({ width: entry.contentRect.width, height: entry.contentRect.height })
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [ref]);
  return size;
}

function Plan({ zone, selected, onSelect }) {
  const t = useT();
  const containerRef = useRef(null);
  const size = useSize(containerRef);
  const [cars, settle] = useCars(zone);
  const count = zone.spots.length;

  const renderSlot = (spot, slot) => {
    const car = cars[slot];
    const filled = car?.phase === "parked";
    return (
      <button
        type="button"
        key={spot.name}
        className={`slot ${filled ? "slot--occupied" : ""} ${spot.status === "error" ? "slot--error" : ""} ${
          selected === spot.code ? "slot--selected" : ""
        }`}
        onClick={() => onSelect(spot.code)}
        aria-label={`${spot.code} ${t(spot.status === "occupied" ? "Occupied" : spot.status === "empty" ? "Free" : "Unknown")}`}
      >
        <span className="slot__code">{car?.phase === "parked" ? "" : spot.code.split("-").pop()}</span>
        {car && (
          <Car
            area={zone.area}
            slot={slot}
            count={count}
            car={car}
            width={size.width}
            onDone={() => settle(slot)}
          />
        )}
      </button>
    );
  };

  return (
    <div className="plan panel" style={{ "--zone": zone.color }}>
      <style>{zone.spots.map((_, slot) => keyframes(zone.area, slot, count, size.height)).join("")}</style>
      <div className="plan__lot" ref={containerRef}>
        <div className="plan__row">{zone.spots.map((s, slot) => isTopRow(slot, count) && renderSlot(s, slot))}</div>
        <div className="plan__lane" />
        <div className="plan__lane plan__lane--entry">
          <span className="caption">{t("Entrance")}</span>
        </div>
        <div className="plan__row plan__row--bottom">
          {zone.spots.map((s, slot) => !isTopRow(slot, count) && renderSlot(s, slot))}
        </div>
      </div>
    </div>
  );
}

function SpotList({ zone, selected, onSelect }) {
  const t = useT();
  const label = { occupied: "Occupied", empty: "Free", error: "Prediction error", unknown: "Unknown" };
  const chip = { occupied: "chip--full", empty: "chip--free", error: "chip--alert", unknown: "chip--neutral" };

  return (
    <div className="panel table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>{t("Spot")}</th>
            <th>{t("Name")}</th>
            <th>{t("Status")}</th>
          </tr>
        </thead>
        <tbody>
          {zone.spots.map((spot) => (
            <tr
              key={spot.name}
              className={selected === spot.code ? "row--selected" : ""}
              onClick={() => onSelect(spot.code)}
              style={{ cursor: "pointer" }}
            >
              <td>
                <b className="code">{spot.code}</b>
              </td>
              <td className="muted">{spot.name}</td>
              <td>
                <span className={`chip ${chip[spot.status]}`}>{t(label[spot.status])}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ZonePlan() {
  const t = useT();
  const ago = useAgo();
  const { area } = useParams();
  const { zone, zones, now } = useZone(area);
  const [selected, setSelected] = useState(null);

  if (!zones) {
    return <span className="skeleton" style={{ height: 420 }} />;
  }
  if (!area || !zone) {
    return zones.length ? <Navigate to={`/zones/${zones[0].area}`} replace /> : <Navigate to="/" replace />;
  }

  const toggle = (code) => setSelected((current) => (current === code ? null : code));

  return (
    <>
      <header className="page__head">
        <div>
          <Link to="/" className="back caption">
            <ArrowLeft size={14} aria-hidden="true" className="flip" /> {t("Zone network")}
          </Link>
          <h1 className="page__title zone-title">
            <span className="zone-dot zone-dot--lg" style={{ background: zone.color }} aria-hidden="true" />
            {zone.code} · {t("Zone {n}", { n: zone.area })}
          </h1>
          <p className="zone-meta muted">
            <StateChip state={zone.state} /> {t("Updated {ago}", { ago: ago(zone.updatedAt, now) })}
          </p>
        </div>
        <p className="total">
          <strong className="num">{zone.free === null ? "—" : zone.free}</strong>
          <span>{t("free spots out of {n}", { n: zone.total })}</span>
        </p>
      </header>

      <nav className="zone-tabs" aria-label={t("Zones")}>
        {zones.map((z) => (
          <NavLink key={z.area} to={`/zones/${z.area}`} className="zone-tab" style={{ "--zone": z.color }}>
            <span className="zone-dot" style={{ background: z.color }} aria-hidden="true" />
            {z.code}
            <span className="num muted">{z.free === null ? "—" : z.free}</span>
          </NavLink>
        ))}
      </nav>

      {zone.total === 0 ? (
        <div className="panel empty">
          <b>{t("No spots in this zone")}</b>
          <p>{t("Draw the spots of this camera on the Spots page.")}</p>
        </div>
      ) : (
        <>
          <Plan key={zone.area} zone={zone} selected={selected} onSelect={toggle} />
          <SpotList zone={zone} selected={selected} onSelect={toggle} />
        </>
      )}
    </>
  );
}
