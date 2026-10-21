import { useState } from "react";
import { Navigate } from "react-router-dom";
import css from "../styles/login.css?inline";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { LanguageSelect, useT } from "../i18n.jsx";
import { useModal } from "../components/Modal.jsx";

const EMPTY_REGISTER = { username: "", password: "", email: "", first_name: "", last_name: "" };

export default function Login() {
  const t = useT();
  const modal = useModal();
  const { user, login } = useAuth();
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [registration, setRegistration] = useState(EMPTY_REGISTER);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const switchMode = (next) => {
    setMode(next);
    setError("");
  };

  const onLogin = async (e) => {
    e.preventDefault();
    const res = await login(credentials.username, credentials.password);
    if (!res.ok) {
      setError(t("Login failed. Please check your credentials and try again."));
    }
  };

  const onRegister = async (e) => {
    e.preventDefault();
    const res = await api("/auth/register/", { method: "POST", body: registration });
    if (!res.ok) {
      setError(t("Registration failed. Please check your credentials and try again."));
      return;
    }
    await modal.notify(t("Registration successful. Please confirm your email."));
    setRegistration(EMPTY_REGISTER);
    switchMode("login");
  };

  const field = (state, setState, name, type, placeholder) => (
    <input
      type={type}
      placeholder={t(placeholder)}
      required
      autoComplete="off"
      value={state[name]}
      onFocus={() => setError("")}
      onChange={(e) => setState({ ...state, [name]: e.target.value })}
    />
  );

  const errorBox = error && (
    <p className="error-message" style={{ display: "block" }}>
      {error}
    </p>
  );

  return (
    <>
      <style>{css}</style>
      <nav className="navbar">
        <div className="navbar__container">
          <a id="navbar__logo">PARKING</a>
        </div>
        <ul className="navbar__menu">
          <li className="navbar__item">
            <LanguageSelect />
          </li>
        </ul>
      </nav>

      <div className="main__container">
        <div className="container">
          <div className={`form-box ${mode === "login" ? "active" : ""}`}>
            <h2>{t("Login")}</h2>
            {errorBox}
            <form onSubmit={onLogin}>
              {field(credentials, setCredentials, "username", "text", "Username")}
              {field(credentials, setCredentials, "password", "password", "Password")}
              <button type="submit" className="submit">
                {t("Login")}
              </button>
              <p>
                {t("Don't have an account ?")}{" "}
                <a href="#" onClick={() => switchMode("register")}>
                  {t("Register")}
                </a>
              </p>
            </form>
          </div>

          <div className={`form-box ${mode === "register" ? "active" : ""}`}>
            <h2>{t("Register")}</h2>
            {errorBox}
            <form onSubmit={onRegister}>
              {field(registration, setRegistration, "username", "text", "Username")}
              {field(registration, setRegistration, "password", "password", "Password")}
              {field(registration, setRegistration, "email", "email", "Email")}
              {field(registration, setRegistration, "first_name", "text", "First Name")}
              {field(registration, setRegistration, "last_name", "text", "Last Name")}
              <button className="submit" type="submit">
                {t("Register")}
              </button>
              <p>
                {t("Already have an account ?")}{" "}
                <a href="#" onClick={() => switchMode("login")}>
                  {t("Login")}
                </a>
              </p>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
