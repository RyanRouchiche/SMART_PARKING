import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { api, openSocket } from "./api.js";
import { ZonesProvider } from "./zones.jsx";

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
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return (
    <ZonesProvider>
      <Outlet />
    </ZonesProvider>
  );
}

export function RequireAdmin() {
  const { user } = useAuth();
  return user.role === "admin" ? <Outlet /> : <Navigate to="/" replace />;
}
