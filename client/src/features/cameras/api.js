import { api } from "../../shared/http.js";

export const listCameras = () => api("/cameras/");

export const addCameras = (cameras) => api("/cameras/", { method: "POST", body: cameras });

export const deleteCamera = (id) => api(`/cameras/${id}/`, { method: "DELETE" });

export const fetchSnapshots = () => api("/parking/snapshots/");

export const fetchLayouts = () => api("/parking/coordinates/");

export const saveLayouts = (layouts) => api("/parking/coordinates/", { method: "POST", body: layouts });
