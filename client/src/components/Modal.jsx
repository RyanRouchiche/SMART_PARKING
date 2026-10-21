import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { useT } from "../i18n.jsx";

const ModalContext = createContext(null);

export function ModalProvider({ children }) {
  const t = useT();
  const [modal, setModal] = useState(null);
  const [input, setInput] = useState("");

  const open = useCallback(
    (type, message) =>
      new Promise((resolve) => {
        setInput("");
        setModal({ type, message, resolve });
      }),
    []
  );

  const api = useMemo(
    () => ({
      notify: (message) => open("notify", message),
      confirm: (message) => open("confirm", message),
      prompt: (message) => open("prompt", message),
    }),
    [open]
  );

  const close = (value) => {
    modal.resolve(value);
    setModal(null);
  };

  return (
    <ModalContext.Provider value={api}>
      {children}
      {modal && (
        <div className="modal-overlay" style={{ display: "flex" }}>
          <div className="modal-content">
            <p>{modal.message}</p>
            {modal.type === "prompt" && (
              <input
                id="inputField"
                autoFocus
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && close(input.trim() || null)}
              />
            )}
            <div className="modal-actions">
              {modal.type === "confirm" && (
                <button className="modal__btn gray" onClick={() => close(false)}>
                  {t("Undo")}
                </button>
              )}
              <button
                className="modal__btn"
                onClick={() =>
                  close(modal.type === "prompt" ? input.trim() || null : true)
                }
              >
                {modal.type === "notify" ? t("Confirm") : t("Yes, Confirm")}
              </button>
            </div>
          </div>
        </div>
      )}
    </ModalContext.Provider>
  );
}

export function useModal() {
  return useContext(ModalContext);
}
