import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth.jsx";
import { LanguageSelect, useT } from "../i18n.jsx";
import { useModal } from "./Modal.jsx";
import css from "../styles/navbar.css?inline";

const LINKS = [
  ["/management", "dashboard"],
  ["/parking", "parking status"],
  ["/setup", "setup"],
  ["/spots", "Initialization"],
  ["/lcd", "LCD"],
];

export default function Navbar() {
  const t = useT();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const modal = useModal();
  const [menuOpen, setMenuOpen] = useState(false);

  const onLogout = async () => {
    if (!(await modal.confirm(t("Are you sure you want to log out?")))) {
      return;
    }
    const res = await logout();
    if (!res.ok) {
      modal.notify(t("Logout failed"));
    }
  };

  return (
    <nav className="navbar">
      <style>{css}</style>
      <div className="navbar__container">
        <Link to="/" id="navbar__logo">
          PARKING
        </Link>
        <div
          className={`navbar__toggle ${menuOpen ? "is-active" : ""}`}
          id="mobile-menu"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          <span className="bar"></span>
          <span className="bar"></span>
          <span className="bar"></span>
        </div>
        <ul className={`navbar__menu ${menuOpen ? "active" : ""}`}>
          {LINKS.map(([path, label]) => (
            <li className="navbar__item" key={path}>
              <button
                className={`navbar__links ${pathname === path ? "active" : ""}`}
                onClick={() => navigate(path)}
              >
                {t(label)}
              </button>
            </li>
          ))}
          <li className="navbar__btn">
            <button className="button" onClick={onLogout}>
              {t("logout")}
            </button>
          </li>
          <li className="navbar__item navbar__item--lang">
            <LanguageSelect />
          </li>
        </ul>
      </div>
    </nav>
  );
}
