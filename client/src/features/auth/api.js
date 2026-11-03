import { api } from "../../shared/http.js";

export const fetchMe = () => api("/auth/me/");

export const login = (username, password) => api("/auth/login/", { method: "POST", body: { username, password } });

export const logout = () => api("/auth/logout/", { method: "POST" });

export const register = (registration) => api("/auth/register/", { method: "POST", body: registration });

export const activate = (uid, token) =>
  api(`/auth/activate/${encodeURIComponent(uid)}/${encodeURIComponent(token)}/`);
