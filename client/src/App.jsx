import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAdmin, RequireAuth } from "./auth.jsx";
import AppShell from "./components/AppShell.jsx";
import Login from "./pages/Login.jsx";
import Activate from "./pages/Activate.jsx";
import Network from "./pages/Network.jsx";
import ZonePlan from "./pages/ZonePlan.jsx";
import Cameras from "./pages/Cameras.jsx";
import SpotPicker from "./pages/SpotPicker.jsx";
import Users from "./pages/Users.jsx";
import Lcd from "./pages/Lcd.jsx";

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
