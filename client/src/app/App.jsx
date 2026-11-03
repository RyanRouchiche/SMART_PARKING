import { Navigate, Route, Routes } from "react-router-dom";
import { Activate, Login, RequireAdmin } from "../features/auth/index.js";
import { Users } from "../features/parking/index.js";
import { Cameras, SpotPicker } from "../features/cameras/index.js";
import { Lcd, Network, ZonePlan } from "../features/detection/index.js";
import AppShell from "./AppShell.jsx";
import RequireAuth from "./RequireAuth.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/activate/:uid/:token" element={<Activate />} />
      <Route element={<RequireAuth />}>
        <Route path="/lcd/:area?" element={<Lcd />} />
        <Route element={<AppShell />}>
          <Route path="/" element={<Network />} />
          <Route path="/zones/:area?" element={<ZonePlan />} />
          <Route element={<RequireAdmin />}>
            <Route path="/cameras" element={<Cameras />} />
            <Route path="/spots" element={<SpotPicker />} />
            <Route path="/users" element={<Users />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
