import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, Outlet } from "react-router-dom";
import * as authApi from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(undefined);

  useEffect(() => {
    authApi.fetchMe().then((res) => setUser(res.ok ? res.data.user : null));
    const onExpired = () => setUser(null);
    window.addEventListener("session-expired", onExpired);
    return () => window.removeEventListener("session-expired", onExpired);
  }, []);

  const login = useCallback(async (username, password) => {
    const res = await authApi.login(username, password);
    if (res.ok) {
      setUser(res.data.user);
    }
    return res;
  }, []);

  const logout = useCallback(async () => {
    const res = await authApi.logout();
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

export function RequireAdmin() {
  const { user } = useAuth();
  return user.role === "admin" ? <Outlet /> : <Navigate to="/" replace />;
}
