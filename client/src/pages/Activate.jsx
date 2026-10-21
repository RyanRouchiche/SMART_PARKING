import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import css from "../styles/login.css?inline";
import { api } from "../api.js";
import { useT } from "../i18n.jsx";

export default function Activate() {
  const t = useT();
  const { uid, token } = useParams();
  const [ok, setOk] = useState(null);

  useEffect(() => {
    api(`/auth/activate/${uid}/${token}/`).then((res) => setOk(res.ok));
  }, [uid, token]);

  return (
    <>
      <style>{css}</style>
      <div className="main__container">
        <div className="container">
          <div className="form-box active">
            {ok !== null && (
              <h2>{t(ok ? "Account activated successfully!" : "Invalid activation link.")}</h2>
            )}
            <p>
              <Link to="/login">{t("Go to login")}</Link>
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
