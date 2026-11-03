import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";
import { AuthLayout } from "./Login.jsx";

export default function Activate() {
  const t = useT();
  const { uid, token } = useParams();
  const [ok, setOk] = useState(null);

  useEffect(() => {
    api(`/auth/activate/${encodeURIComponent(uid)}/${encodeURIComponent(token)}/`).then((res) => setOk(res.ok));
  }, [uid, token]);

  return (
    <AuthLayout>
      <div className="stack-form">
        {ok === null ? (
          <span className="skeleton" style={{ width: 240, height: 28 }} />
        ) : (
          <>
            <h1 className="page__title">{t(ok ? "Account activated" : "Invalid activation link")}</h1>
            <p className="muted">
              {t(ok ? "You can now log in." : "The link has expired or was already used. Ask an administrator for a new one.")}
            </p>
          </>
        )}
        <Link to="/login" className="btn btn--primary btn--block">
          {t("Go to login")}
        </Link>
      </div>
    </AuthLayout>
  );
}
