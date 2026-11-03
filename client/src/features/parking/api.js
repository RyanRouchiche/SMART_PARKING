import { api } from "../../shared/http.js";

export const listOperators = () => api("/users/");

export const createOperator = (guest) => api("/users/", { method: "POST", body: guest });

export const deleteOperator = (id) => api(`/users/${id}/`, { method: "DELETE" });

export const listAreas = () => api("/parking/areas/");
