import { useCallback, useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { createOperator, deleteOperator, listOperators } from "../api.js";
import { useT } from "../../../shared/i18n.jsx";
import { useFeedback } from "../../../shared/ui/Feedback.jsx";
import "../../../shared/styles/forms.css";

const EMPTY_GUEST = { username: "", email: "", first_name: "", last_name: "", password: "" };
const FIELDS = [
  ["username", "text", "Username", "username"],
  ["email", "email", "Email", "email"],
  ["first_name", "text", "First name", "given-name"],
  ["last_name", "text", "Last name", "family-name"],
  ["password", "password", "Temporary password", "new-password"],
];

function fieldErrors(data) {
  if (!data || typeof data !== "object") {
    return {};
  }
  return Object.fromEntries(
    Object.entries(data)
      .filter(([, value]) => Array.isArray(value))
      .map(([key, value]) => [key, value.join(" ")])
  );
}

export default function Users() {
  const t = useT();
  const feedback = useFeedback();
  const [users, setUsers] = useState(null);
  const [guest, setGuest] = useState(EMPTY_GUEST);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const res = await listOperators();
    setUsers(res.ok ? res.data.users : []);
  }, []);

  useEffect(() => {
    load();
    const onStatus = ({ detail }) =>
      setUsers((list) => list?.map((u) => (u.id === detail.user_id ? { ...u, status: detail.status } : u)));
    window.addEventListener("user-status", onStatus);
    return () => window.removeEventListener("user-status", onStatus);
  }, [load]);

  const create = async (e) => {
    e.preventDefault();
    setSaving(true);
    const res = await createOperator(guest);
    setSaving(false);
    if (!res.ok) {
      setErrors(fieldErrors(res.data));
      feedback.toast(t("The guest could not be created. Check the highlighted fields."), { error: true });
      return;
    }
    feedback.toast(t("Guest created. An activation email has been sent to {email}.", { email: guest.email }));
    setGuest(EMPTY_GUEST);
    setErrors({});
    load();
  };

  const remove = async (user) => {
    const ok = await feedback.confirm({
      message: t("Delete the account of {name}?", { name: user.username }),
      confirmLabel: t("Delete"),
      danger: true,
    });
    if (!ok) {
      return;
    }
    const res = await deleteOperator(user.id);
    feedback.toast(t(res.ok ? "Account deleted." : "Could not delete this account."), { error: !res.ok });
    if (res.ok) {
      load();
    }
  };

  return (
    <>
      <header className="page__head">
        <div>
          <h1 className="page__title">{t("Users")}</h1>
          <p className="muted">{t("Guests can view the network, the zones and the LCD screen.")}</p>
        </div>
      </header>

      <div className="split">
        <form className="panel panel--pad stack" onSubmit={create}>
          <h2 className="heading">{t("Create a guest")}</h2>
          {FIELDS.map(([name, type, label, autoComplete]) => (
            <div className="field" key={name}>
              <label htmlFor={`guest-${name}`}>{t(label)}</label>
              <input
                id={`guest-${name}`}
                className="input"
                type={type}
                required
                autoComplete={autoComplete}
                value={guest[name]}
                aria-invalid={Boolean(errors[name])}
                onChange={(e) => setGuest({ ...guest, [name]: e.target.value })}
              />
              {errors[name] && <p className="field__error">{errors[name]}</p>}
            </div>
          ))}
          <button type="submit" className="btn btn--primary" disabled={saving}>
            {saving ? t("Creating…") : t("Create the guest")}
          </button>
        </form>

        <div className="panel table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>{t("Username")}</th>
                <th>{t("Name")}</th>
                <th>{t("Email")}</th>
                <th>{t("Status")}</th>
                <th className="right">
                  <span className="visually-hidden">{t("Actions")}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {users === null ? (
                [0, 1, 2].map((i) => (
                  <tr key={i}>
                    {[100, 140, 180, 70, 40].map((w, j) => (
                      <td key={j}>
                        <span className="skeleton" style={{ width: w }} />
                      </td>
                    ))}
                  </tr>
                ))
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <div className="empty">
                      <b>{t("No guest yet")}</b>
                      {t("Create one with the form to give someone read-only access.")}
                    </div>
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <b>{u.username}</b>
                    </td>
                    <td>
                      {u.first_name} {u.last_name}
                    </td>
                    <td className="muted">{u.email}</td>
                    <td>
                      <span className={`chip ${u.status === "Online" ? "chip--free" : "chip--offline"}`}>
                        {t(u.status === "Online" ? "Online" : "Offline")}
                      </span>
                    </td>
                    <td className="right">
                      <button type="button" className="btn btn--ghost" onClick={() => remove(u)}>
                        <Trash2 size={16} aria-hidden="true" />
                        {t("Delete")}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
