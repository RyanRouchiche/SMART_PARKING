import { useEffect } from "react";
import { openSocket } from "../../shared/http.js";

export function usePresence(enabled) {
  useEffect(() => {
    if (!enabled) {
      return;
    }
    const socket = openSocket("user-status/");
    socket.onmessage = (event) =>
      window.dispatchEvent(new CustomEvent("user-status", { detail: JSON.parse(event.data) }));
    return () => socket.close();
  }, [enabled]);
}
