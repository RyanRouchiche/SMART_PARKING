import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { api, openSocket } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    api("/auth/me/").then((res) => setUser(res.ok ? res.data.user : null));
    const onExpired = () => setUser(null);
    window.addEventListener("session-expired", onExpired);
    return () => window.removeEventListener("session-expired", onExpired);
  }, []);

  const login = useCallback(async (username, password) => {
    const res = await api("/auth/login/", {
      method: "POST",
      body: { username, password },
    });
    if (res.ok) {
      setUser(res.data.user);
    }
    return res;
  }, []);

  const logout = useCallback(async () => {
    const res = await api("/auth/logout/", { method: "POST" });
    setUser(null);
    return res;
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function RequireAuth() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      return;
    }
    const socket = openSocket("user-status/");
    socket.onmessage = (event) =>
      window.dispatchEvent(
        new CustomEvent("user-status", { detail: JSON.parse(event.data) })
      );
    return () => socket.close();
  }, [user]);

  if (user === undefined) {
    return null;
  }
  return user ? <Outlet /> : <Navigate to="/login" replace />;
}
