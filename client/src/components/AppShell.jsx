import { NavLink, Outlet } from "react-router-dom";
import { Camera, LayoutGrid, LogOut, Monitor, Network, SquareDashedMousePointer, Users } from "lucide-react";
import { useAuth } from "../auth.jsx";
import { LanguageSelect, useT } from "../i18n.jsx";
import { useFeedback } from "./Feedback.jsx";

const LINKS = [
  { to: "/", label: "Network", icon: Network, end: true },
  { to: "/zones", label: "Zones", icon: LayoutGrid },
  { to: "/cameras", label: "Cameras", icon: Camera, admin: true },
  { to: "/spots", label: "Spots", icon: SquareDashedMousePointer, admin: true },
  { to: "/users", label: "Users", icon: Users, admin: true },
  { to: "/lcd", label: "LCD screen", icon: Monitor },
];

export default function AppShell() {
  const t = useT();
  const { user, logout } = useAuth();
  const feedback = useFeedback();
  const isAdmin = user.role === "admin";

  const onLogout = async () => {
    const ok = await feedback.confirm({ message: t("Log out of Smart Parking?"), confirmLabel: t("Log out") });
    if (ok && !(await logout()).ok) {
      feedback.toast(t("Logout failed"), { error: true });
    }
  };

  return (
    <div className="shell">
      <nav className="rail" aria-label={t("Main navigation")}>
        <NavLink to="/" className="rail__brand">
          <span className="rail__mark">P</span>
          <span className="rail__label">Smart Parking</span>
        </NavLink>
        {LINKS.filter((link) => isAdmin || !link.admin).map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end} className="rail__link">
            <Icon size={18} strokeWidth={1.75} aria-hidden="true" />
            <span className="rail__label">{t(label)}</span>
          </NavLink>
        ))}
        <div className="rail__foot">
          <p className="rail__user">
            <b>{user.username}</b>
            {t(isAdmin ? "Administrator" : "Guest")}
          </p>
          <LanguageSelect />
          <button type="button" className="rail__button" onClick={onLogout}>
            <LogOut size={16} strokeWidth={1.75} aria-hidden="true" />
            <span className="rail__label">{t("Log out")}</span>
          </button>
        </div>
      </nav>
      <main className="page">
        <Outlet />
      </main>
    </div>
  );
}
