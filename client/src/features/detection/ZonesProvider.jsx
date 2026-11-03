import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { openSocket } from "../../shared/http.js";
import { LINE_COUNT, lineColor, spotCode } from "../../shared/zones/style.js";
import { fetchLayouts } from "../cameras/index.js";
import { listAreas } from "../parking/index.js";

const STALE_AFTER_MS = 30000;
const RETRY_AFTER_MS = 15000;

const ZonesContext = createContext(null);

function useNow(intervalMs) {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);
  return now;
}

function useFeed(area) {
  const [feed, setFeed] = useState({ status: "connecting", spots: [], updatedAt: null });

  useEffect(() => {
    let socket;
    let retry;
    let closed = false;

    const connect = () => {
      socket = openSocket(`video/${area}/`);
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setFeed({ status: "live", spots: data.spot_details, updatedAt: Date.now() });
      };
      socket.onclose = () => {
        if (closed) {
          return;
        }
        setFeed((current) => ({ ...current, status: "offline" }));
        retry = setTimeout(connect, RETRY_AFTER_MS);
      };
    };

    connect();
    return () => {
      closed = true;
      clearTimeout(retry);
      socket?.close();
    };
  }, [area]);

  return feed;
}

function FeedSubscriber({ area, onFeed }) {
  const feed = useFeed(area);
  useEffect(() => onFeed(area, feed), [area, feed, onFeed]);
  return null;
}

export function ZonesProvider({ children }) {
  const [layout, setLayout] = useState(null);
  const [feeds, setFeeds] = useState({});
  const now = useNow(5000);

  useEffect(() => {
    Promise.all([listAreas(), fetchLayouts()]).then(([areasRes, coordsRes]) => {
      const coordinates = coordsRes.ok ? coordsRes.data.data : [];
      const areas = areasRes.ok ? areasRes.data.areas : [];
      setLayout(
        areas.map((area) => {
          const entry = coordinates.find((c) => Number(c.area) === area);
          return { area, spotNames: entry ? Object.keys(entry.coordinates) : [] };
        })
      );
    });
  }, []);

  const onFeed = useMemo(
    () => (area, feed) => setFeeds((current) => (current[area] === feed ? current : { ...current, [area]: feed })),
    []
  );

  const zones = useMemo(() => {
    if (!layout) {
      return null;
    }
    return layout.map(({ area, spotNames }) => {
      const feed = feeds[area] ?? { status: "connecting", spots: [], updatedAt: null };
      const stale = feed.status === "live" && now - feed.updatedAt > STALE_AFTER_MS;
      const statusByName = Object.fromEntries(feed.spots.map((s) => [s.spot, s.status]));
      const names = feed.spots.length ? feed.spots.map((s) => s.spot) : spotNames;
      const spots = names.map((name) => ({
        name,
        code: spotCode(area, name),
        status: statusByName[name] ?? "unknown",
      }));
      const free = spots.filter((s) => s.status === "empty").length;
      const errors = spots.filter((s) => s.status === "error").length;
      const known = feed.status === "live" && !stale;
      let state = "connecting";
      if (feed.status === "offline") state = "offline";
      else if (stale) state = "stale";
      else if (known && errors) state = "error";
      else if (known && free === 0 && spots.length) state = "full";
      else if (known) state = "ok";
      return {
        area,
        code: `Z${area}`,
        color: lineColor(area),
        dashed: area > LINE_COUNT,
        spots,
        total: spots.length,
        free: known || stale ? free : null,
        occupied: spots.filter((s) => s.status === "occupied").length,
        errors,
        state,
        updatedAt: feed.updatedAt,
      };
    });
  }, [layout, feeds, now]);

  return (
    <ZonesContext.Provider value={{ zones, now }}>
      {layout?.map(({ area }) => (
        <FeedSubscriber key={area} area={area} onFeed={onFeed} />
      ))}
      {children}
    </ZonesContext.Provider>
  );
}

export function useZones() {
  return useContext(ZonesContext);
}

export function useZone(area) {
  const { zones, now } = useZones();
  return { zone: zones?.find((z) => z.area === Number(area)) ?? null, zones, now };
}
