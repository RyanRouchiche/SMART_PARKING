import { api } from "../../shared/http.js";

export const getStats = (days) => api(`/parking/stats/?days=${days}`);
