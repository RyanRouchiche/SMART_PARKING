import { useEffect, useMemo, useState } from "react";
import { getStats } from "../api.js";
import { useLanguage, useT } from "../../../shared/i18n.jsx";
import "./stats.css";

const PERIODS = [7, 30, 90];
const HOURS = Array.from({ length: 24 }, (_, h) => h);

const weekdayOf = (date) => (new Date(`${date}T12:00:00`).getDay() + 6) % 7;
const mean = (values) => (values.length ? values.reduce((a, b) => a + b, 0) / values.length : null);

function summarize(rows) {
  const cells = Array.from({ length: 7 }, () => HOURS.map(() => []));
  const byHour = HOURS.map(() => []);
  const byWeekday = Array.from({ length: 7 }, () => []);
  const byDay = new Map();
  for (const [date, hour, occupancy] of rows) {
    const weekday = weekdayOf(date);
    cells[weekday][hour].push(occupancy);
    byHour[hour].push(occupancy);
    byWeekday[weekday].push(occupancy);
    byDay.set(date, [...(byDay.get(date) ?? []), occupancy]);
  }
  const hourMeans = byHour.map(mean);
  const weekdayMeans = byWeekday.map(mean);
  const best = (list) => list.reduce((top, v, i) => (v !== null && (top === -1 || v > list[top]) ? i : top), -1);
  return {
    average: mean(rows.map((r) => r[2])),
    peakHour: best(hourMeans),
    peakHourValue: hourMeans[best(hourMeans)],
    busiestDay: best(weekdayMeans),
    busiestDayValue: weekdayMeans[best(weekdayMeans)],
    grid: cells.map((row) => row.map(mean)),
    days: [...byDay].map(([date, values]) => ({ date, value: mean(values) })),
  };
}

export default function Stats() {
  const t = useT();
  const lang = useLanguage();
  const [days, setDays] = useState(90);
  const [rows, setRows] = useState(null);
  const [failed, setFailed] = useState(false);
  const [readout, setReadout] = useState(null);
  const [dayReadout, setDayReadout] = useState(null);

  useEffect(() => {
    let live = true;
    setRows(null);
    setFailed(false);
    getStats(days).then((res) => {
      if (!live) return;
      if (res.ok) setRows(res.data.hours);
      else setFailed(true);
    });
    return () => {
      live = false;
    };
  }, [days]);

  const locale = lang === "ar" ? "ar-DZ" : lang === "fr" ? "fr-FR" : "en-GB";
  const weekdayNames = useMemo(() => {
    const format = new Intl.DateTimeFormat(locale, { weekday: "long" });
    return Array.from({ length: 7 }, (_, i) => format.format(new Date(2026, 10, 2 + i)));
  }, [locale]);
  const pct = useMemo(() => {
    const format = new Intl.NumberFormat(locale, { style: "percent", maximumFractionDigits: 0 });
    return (value) => format.format(value / 100);
  }, [locale]);
  const dayFormat = useMemo(() => new Intl.DateTimeFormat(locale, { day: "numeric", month: "short" }), [locale]);
  const summary = useMemo(() => (rows?.length ? summarize(rows) : null), [rows]);

  return (
    <>
      <header className="page__head">
        <div>
          <h1 className="page__title">{t("Statistics")}</h1>
          <p className="muted">{t("Share of occupied spots, from the detection history.")}</p>
        </div>
        <div className="periods" role="group" aria-label={t("Period")}>
          {PERIODS.map((p) => (
            <button
              key={p}
              type="button"
              className={`btn ${p === days ? "btn--primary" : "btn--secondary"}`}
              aria-pressed={p === days}
              onClick={() => setDays(p)}
            >
              {t("{n} days", { n: p })}
            </button>
          ))}
        </div>
      </header>

      {failed && <div className="panel panel--pad">{t("Could not load the statistics.")}</div>}
      {!failed && rows === null && <div className="panel panel--pad muted">{t("Loading…")}</div>}
      {!failed && rows?.length === 0 && (
        <div className="panel panel--pad empty">{t("No history yet. Statistics appear after the first hour of detection.")}</div>
      )}

      {summary && (
        <>
          <section className="kpis">
            <div className="panel panel--pad kpi">
              <p className="caption">{t("Average occupancy")}</p>
              <p className="kpi__value">{pct(summary.average)}</p>
            </div>
            <div className="panel panel--pad kpi">
              <p className="caption">{t("Peak hour")}</p>
              <p className="kpi__value">{t("{h} h", { h: summary.peakHour })}</p>
              <p className="muted">{t("{value} occupied on average", { value: pct(summary.peakHourValue) })}</p>
            </div>
            <div className="panel panel--pad kpi">
              <p className="caption">{t("Busiest day")}</p>
              <p className="kpi__value kpi__value--word">{weekdayNames[summary.busiestDay]}</p>
              <p className="muted">{t("{value} occupied on average", { value: pct(summary.busiestDayValue) })}</p>
            </div>
          </section>

          <section className="panel panel--pad stack">
            <div className="chart-head">
              <h2 className="heading">{t("Typical week")}</h2>
              <p className="readout" aria-live="polite">{readout ?? t("Hover a cell to see its value.")}</p>
            </div>
            <div className="heat-wrap">
              <table className="heat">
                <caption className="visually-hidden">{t("Average occupancy by day and hour")}</caption>
                <thead>
                  <tr>
                    <th scope="col" className="heat__corner"><span className="visually-hidden">{t("Day")}</span></th>
                    {HOURS.map((h) => (
                      <th key={h} scope="col" className="heat__hour">{h % 3 === 0 ? h : ""}<span className="visually-hidden">{h % 3 === 0 ? "" : h}</span></th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {summary.grid.map((row, weekday) => (
                    <tr key={weekday}>
                      <th scope="row" className="heat__day">{weekdayNames[weekday]}</th>
                      {row.map((value, hour) => {
                        const label = `${weekdayNames[weekday]} ${t("{h} h", { h: hour })} : ${value === null ? t("no data") : pct(value)}`;
                        return (
                          <td
                            key={hour}
                            className={`heat__cell${value === null ? " heat__cell--none" : ""}`}
                            style={value === null ? undefined : { "--level": `${Math.round(value)}%` }}
                            title={label}
                            onMouseEnter={() => setReadout(label)}
                            onMouseLeave={() => setReadout(null)}
                          >
                            <span className="visually-hidden">{value === null ? t("no data") : pct(value)}</span>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="legend" aria-hidden="true">
              <span>{pct(0)}</span>
              <span className="legend__ramp" />
              <span>{pct(100)}</span>
              <span className="legend__none" />
              <span>{t("no data (closed or offline)")}</span>
            </div>
          </section>

          <section className="panel panel--pad stack">
            <div className="chart-head">
              <h2 className="heading">{t("Average occupancy per day")}</h2>
              <p className="readout" aria-live="polite">{dayReadout ?? t("Hover a bar to see its value.")}</p>
            </div>
            <div className="bars-plot">
            <div className="bars__scale" aria-hidden="true"><span>{pct(100)}</span><span>{pct(50)}</span><span>{pct(0)}</span></div>
            <div className="bars" role="list">
              {summary.days.map(({ date, value }) => {
                const label = `${dayFormat.format(new Date(`${date}T12:00:00`))} : ${pct(value)}`;
                return (
                  <div
                    key={date}
                    role="listitem"
                    className="bars__slot"
                    title={label}
                    aria-label={label}
                    onMouseEnter={() => setDayReadout(label)}
                    onMouseLeave={() => setDayReadout(null)}
                  >
                    <span className="bars__bar" style={{ height: `${Math.max(value, 1)}%` }} />
                  </div>
                );
              })}
            </div>
            <div className="bars__axis muted">
              <span>{dayFormat.format(new Date(`${summary.days[0].date}T12:00:00`))}</span>
              <span>{dayFormat.format(new Date(`${summary.days.at(-1).date}T12:00:00`))}</span>
            </div>
            </div>
          </section>
        </>
      )}
    </>
  );
}
