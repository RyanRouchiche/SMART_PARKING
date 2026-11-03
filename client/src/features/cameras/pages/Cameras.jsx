import { useCallback, useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { addCameras, deleteCamera, listCameras } from "../api.js";
import { useT } from "../../../shared/i18n.jsx";
import { useFeedback } from "../../../shared/ui/Feedback.jsx";
import "../../../shared/styles/forms.css";

const MAX_DRAFTS = 10;
let draftId = 0;
const newDraft = () => ({ id: draftId++, area: "", ref: "", path: "" });

function validate(draft) {
  const errors = {};
  if (!/^\d+$/.test(draft.area.trim())) errors.area = "Enter a zone number.";
  if (!draft.ref.trim()) errors.ref = "Enter a reference, for example CAM-01.";
  if (!draft.path.trim()) errors.path = "Enter the RTSP or HTTP address of the stream.";
  return errors;
}

function SkeletonRows() {
  return [0, 1, 2].map((i) => (
    <tr key={i}>
      {[80, 60, 260, 90, 40].map((w, j) => (
        <td key={j}>
          <span className="skeleton" style={{ width: w }} />
        </td>
      ))}
    </tr>
  ));
}

export default function Cameras() {
  const t = useT();
  const feedback = useFeedback();
  const [cameras, setCameras] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const res = await listCameras();
    setCameras(res.ok ? res.data.cameras : []);
    if (!res.ok) {
      feedback.toast(t("Could not load the cameras."), { error: true });
    }
  }, [feedback, t]);

  useEffect(() => {
    load();
  }, [load]);

  const update = (id, name, value) => setDrafts((list) => list.map((d) => (d.id === id ? { ...d, [name]: value } : d)));

  const save = async (e) => {
    e.preventDefault();
    const found = Object.fromEntries(drafts.map((d) => [d.id, validate(d)]).filter(([, errs]) => Object.keys(errs).length));
    setErrors(found);
    if (Object.keys(found).length) {
      return;
    }
    setSaving(true);
    const res = await addCameras(drafts.map(({ area, ref, path }) => ({ area: Number(area), ref: ref.trim(), path: path.trim() })));
    setSaving(false);
    if (!res.ok) {
      feedback.toast(t("The cameras could not be saved."), { error: true });
      return;
    }
    feedback.toast(t("{n} camera(s) added.", { n: drafts.length }));
    setDrafts([]);
    load();
  };

  const remove = async (camera) => {
    const ok = await feedback.confirm({
      message: t("Delete camera {ref}?", { ref: camera.ref }),
      confirmLabel: t("Delete"),
      danger: true,
    });
    if (!ok) {
      return;
    }
    const res = await deleteCamera(camera.id);
    feedback.toast(t(res.ok ? "Camera {ref} deleted." : "Could not delete camera {ref}.", { ref: camera.ref }), { error: !res.ok });
    if (res.ok) {
      load();
    }
  };

  return (
    <>
      <header className="page__head">
        <div>
          <h1 className="page__title">{t("Cameras")}</h1>
          <p className="muted">{t("One camera films one zone. Checking each stream can take a few seconds.")}</p>
        </div>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => setDrafts((list) => [...list, newDraft()])}
          disabled={drafts.length >= MAX_DRAFTS}
        >
          <Plus size={16} aria-hidden="true" />
          {drafts.length >= MAX_DRAFTS ? t("10 cameras at a time") : t("Add a camera")}
        </button>
      </header>

      {drafts.length > 0 && (
        <form className="panel panel--pad draft-form" onSubmit={save} noValidate>
          <h2 className="heading">{t("New cameras")}</h2>
          {drafts.map((draft) => (
            <div className="draft-row" key={draft.id}>
              {[
                ["area", "Zone", "1"],
                ["ref", "Reference", "CAM-01"],
                ["path", "Stream address", "rtsp://192.168.1.20/stream"],
              ].map(([name, label, placeholder]) => (
                <div className={`field field--${name}`} key={name}>
                  <label htmlFor={`${name}-${draft.id}`}>{t(label)}</label>
                  <input
                    id={`${name}-${draft.id}`}
                    className="input"
                    value={draft[name]}
                    placeholder={placeholder}
                    inputMode={name === "area" ? "numeric" : undefined}
                    autoComplete="off"
                    aria-invalid={Boolean(errors[draft.id]?.[name])}
                    onChange={(e) => update(draft.id, name, e.target.value)}
                  />
                  {errors[draft.id]?.[name] && <p className="field__error">{t(errors[draft.id][name])}</p>}
                </div>
              ))}
              <button
                type="button"
                className="btn btn--ghost draft-row__remove"
                aria-label={t("Remove this row")}
                onClick={() => setDrafts((list) => list.filter((d) => d.id !== draft.id))}
              >
                <X size={16} aria-hidden="true" />
              </button>
            </div>
          ))}
          <div className="form-actions">
            <button type="button" className="btn btn--secondary" onClick={() => setDrafts([])}>
              {t("Cancel")}
            </button>
            <button type="submit" className="btn btn--primary" disabled={saving}>
              {saving ? t("Saving…") : t("Save {n} camera(s)", { n: drafts.length })}
            </button>
          </div>
        </form>
      )}

      <div className="panel table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>{t("Reference")}</th>
              <th>{t("Zone")}</th>
              <th>{t("Stream address")}</th>
              <th>{t("Status")}</th>
              <th className="right">
                <span className="visually-hidden">{t("Actions")}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {cameras === null ? (
              <SkeletonRows />
            ) : cameras.length === 0 ? (
              <tr>
                <td colSpan={5}>
                  <div className="empty">
                    <b>{t("No camera yet")}</b>
                    {t("Add the first one to see its zone appear on the network.")}
                  </div>
                </td>
              </tr>
            ) : (
              cameras.map((camera) => (
                <tr key={camera.id}>
                  <td>
                    <b>{camera.ref}</b>
                  </td>
                  <td className="code">Z{camera.area}</td>
                  <td className="path-cell muted">{camera.path}</td>
                  <td>
                    <span className={`chip ${camera.is_active ? "chip--free" : "chip--offline"}`}>
                      {t(camera.is_active ? "Stream OK" : "No stream")}
                    </span>
                  </td>
                  <td className="right">
                    <button type="button" className="btn btn--ghost" onClick={() => remove(camera)}>
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
    </>
  );
}
