import { useState } from "react";
import { Navigate } from "react-router-dom";
import { api } from "../api.js";
import { useAuth } from "../auth.jsx";
import { LanguageSelect, useT } from "../i18n.jsx";
import { useFeedback } from "../components/Feedback.jsx";
import "../styles/auth.css";

const EMPTY_REGISTRATION = { username: "", password: "", email: "", first_name: "", last_name: "" };
const REGISTER_FIELDS = [
  ["username", "text", "Username", "username"],
  ["email", "email", "Email", "email"],
  ["first_name", "text", "First name", "given-name"],
  ["last_name", "text", "Last name", "family-name"],
  ["password", "password", "Password", "new-password"],
];

export function AuthLayout({ children }) {
  const t = useT();
  return (
    <div className="auth">
      <aside className="auth__brand">
        <p className="auth__logo">
          <span className="rail__mark">P</span> Smart Parking
        </p>
        <div className="auth__line" aria-hidden="true">
          {[1, 2, 3, 4].map((n) => (
            <span key={n} className="auth__stop" style={{ "--zone": `var(--line-${n})` }}>
              <i />
              <b>Z{n}</b>
            </span>
          ))}
        </div>
        <p className="auth__pitch">{t("Free spots in real time, zone by zone, from your existing cameras.")}</p>
      </aside>
      <main className="auth__main">
        <div className="auth__lang">
          <LanguageSelect />
        </div>
        <div className="auth__card">{children}</div>
      </main>
    </div>
  );
}

export default function Login() {
  const t = useT();
  const feedback = useFeedback();
  const { user, login } = useAuth();
  const [mode, setMode] = useState("login");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [credentials, setCredentials] = useState({ username: "", password: "" });
  const [registration, setRegistration] = useState(EMPTY_REGISTRATION);

  if (user) {
    return <Navigate to="/" replace />;
  }

  const switchMode = (next) => {
    setMode(next);
    setError("");
  };

  const onLogin = async (e) => {
    e.preventDefault();
    setBusy(true);
    const res = await login(credentials.username, credentials.password);
    setBusy(false);
    if (!res.ok) {
      setError(
        res.status === 401 && res.data?.error?.includes("validation")
          ? t("This account is not activated yet. Open the link sent by email.")
          : t("Wrong username or password.")
      );
    }
  };

  const onRegister = async (e) => {
    e.preventDefault();
    setBusy(true);
    const res = await api("/auth/register/", { method: "POST", body: registration });
    setBusy(false);
    if (!res.ok) {
      const first = res.data && typeof res.data === "object" ? Object.values(res.data).flat()[0] : null;
      setError(first ? String(first) : t("Registration failed. Check the fields and try again."));
      return;
    }
    feedback.toast(t("Account created. Open the activation link sent to {email}.", { email: registration.email }));
    setRegistration(EMPTY_REGISTRATION);
    switchMode("login");
  };

  const field = (state, setState, [name, type, label, autoComplete]) => (
    <div className="field" key={name}>
      <label htmlFor={`${mode}-${name}`}>{t(label)}</label>
      <input
        id={`${mode}-${name}`}
        className="input"
        type={type}
        required
        autoComplete={autoComplete}
        value={state[name]}
        onChange={(e) => {
          setError("");
          setState({ ...state, [name]: e.target.value });
        }}
      />
    </div>
  );

  return (
    <AuthLayout>
      {mode === "login" ? (
        <form className="stack-form" onSubmit={onLogin}>
          <h1 className="page__title">{t("Log in")}</h1>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {field(credentials, setCredentials, ["username", "text", "Username", "username"])}
          {field(credentials, setCredentials, ["password", "password", "Password", "current-password"])}
          <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
            {busy ? t("Logging in…") : t("Log in")}
          </button>
          <p className="muted switch">
            {t("No account yet?")}{" "}
            <button type="button" className="link" onClick={() => switchMode("register")}>
              {t("Create an administrator account")}
            </button>
          </p>
        </form>
      ) : (
        <form className="stack-form" onSubmit={onRegister}>
          <h1 className="page__title">{t("Create an account")}</h1>
          {error && (
            <p className="form-error" role="alert">
              {error}
            </p>
          )}
          {REGISTER_FIELDS.map((f) => field(registration, setRegistration, f))}
          <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
            {busy ? t("Creating…") : t("Create the account")}
          </button>
          <p className="muted switch">
            {t("Already have an account?")}{" "}
            <button type="button" className="link" onClick={() => switchMode("login")}>
              {t("Log in")}
            </button>
          </p>
        </form>
      )}
    </AuthLayout>
  );
}
