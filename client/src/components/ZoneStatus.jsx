import { CircleAlert, CircleCheck, CircleOff, LoaderCircle } from "lucide-react";
import { useT } from "../i18n.jsx";

const CHIPS = {
  ok: { className: "chip--free", icon: CircleCheck, label: "Available" },
  full: { className: "chip--full", icon: CircleCheck, label: "Full" },
  error: { className: "chip--alert", icon: CircleAlert, label: "Prediction error" },
  stale: { className: "chip--alert", icon: CircleAlert, label: "Data delayed" },
  offline: { className: "chip--offline", icon: CircleOff, label: "Offline" },
  connecting: { className: "chip--neutral", icon: LoaderCircle, label: "Connecting" },
};

export function isAlert(state) {
  return state === "offline" || state === "stale" || state === "error";
}

export function StateChip({ state }) {
  const t = useT();
  const { className, icon: Icon, label } = CHIPS[state];
  return (
    <span className={`chip ${className}`}>
      <Icon size={14} strokeWidth={2} aria-hidden="true" />
      {t(label)}
    </span>
  );
}

export function useAgo() {
  const t = useT();
  return (timestamp, now) => {
    if (!timestamp) {
      return t("no data yet");
    }
    const seconds = Math.max(0, Math.round((now - timestamp) / 1000));
    if (seconds < 60) {
      return t("{n} s ago", { n: seconds });
    }
    return t("{n} min ago", { n: Math.round(seconds / 60) });
  };
}
