import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { X } from "lucide-react";
import { useT } from "../i18n.jsx";

const FeedbackContext = createContext(null);
const TOAST_MS = 4000;

function Dialog({ dialog, onClose }) {
  const t = useT();
  const [value, setValue] = useState(dialog.defaultValue ?? "");
  const confirmRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    (inputRef.current ?? confirmRef.current)?.focus();
    inputRef.current?.select();
    const onKey = (e) => e.key === "Escape" && onClose(dialog.type === "prompt" ? null : false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialog, onClose]);

  const submit = (e) => {
    e.preventDefault();
    onClose(dialog.type === "prompt" ? value.trim() || null : true);
  };

  return (
    <div className="dialog-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose(dialog.type === "prompt" ? null : false)}>
      <form className="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title" onSubmit={submit}>
        <h2 id="dialog-title" className="heading">
          {dialog.message}
        </h2>
        {dialog.type === "prompt" && (
          <input ref={inputRef} className="input" value={value} onChange={(e) => setValue(e.target.value)} />
        )}
        <div className="dialog__actions">
          <button type="button" className="btn btn--secondary" onClick={() => onClose(dialog.type === "prompt" ? null : false)}>
            {t("Cancel")}
          </button>
          <button ref={confirmRef} type="submit" className={`btn ${dialog.danger ? "btn--danger" : "btn--primary"}`}>
            {dialog.confirmLabel ?? t("Confirm")}
          </button>
        </div>
      </form>
    </div>
  );
}

export function FeedbackProvider({ children }) {
  const t = useT();
  const [toasts, setToasts] = useState([]);
  const [dialog, setDialog] = useState(null);
  const nextId = useRef(0);

  const dismiss = useCallback((id) => setToasts((list) => list.filter((toast) => toast.id !== id)), []);

  const toast = useCallback(
    (message, { error = false } = {}) => {
      const id = nextId.current++;
      setToasts((list) => [...list, { id, message, error }]);
      setTimeout(() => dismiss(id), TOAST_MS);
    },
    [dismiss]
  );

  const ask = useCallback((type, options) => new Promise((resolve) => setDialog({ type, ...options, resolve })), []);

  const value = useMemo(
    () => ({
      toast,
      confirm: (options) => ask("confirm", options),
      prompt: (options) => ask("prompt", options),
    }),
    [toast, ask]
  );

  const close = useCallback(
    (result) => {
      dialog.resolve(result);
      setDialog(null);
    },
    [dialog]
  );

  return (
    <FeedbackContext.Provider value={value}>
      {children}
      {dialog && <Dialog dialog={dialog} onClose={close} />}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((item) => (
          <div key={item.id} className={`toast ${item.error ? "toast--error" : ""}`}>
            <p>{item.message}</p>
            <button type="button" aria-label={t("Close")} onClick={() => dismiss(item.id)}>
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </FeedbackContext.Provider>
  );
}

export function useFeedback() {
  return useContext(FeedbackContext);
}
