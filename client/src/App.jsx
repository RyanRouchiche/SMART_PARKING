import { Navigate, Route, Routes } from "react-router-dom";
import { RequireAuth } from "./auth.jsx";
import Login from "./pages/Login.jsx";
import Activate from "./pages/Activate.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ParkingStatus from "./pages/ParkingStatus.jsx";
import CameraSetup from "./pages/CameraSetup.jsx";
import SpotPicker from "./pages/SpotPicker.jsx";
import Management from "./pages/Management.jsx";
import Lcd from "./pages/Lcd.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/activate/:uid/:token" element={<Activate />} />
      <Route element={<RequireAuth />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/parking" element={<ParkingStatus />} />
        <Route path="/setup" element={<CameraSetup />} />
        <Route path="/spots" element={<SpotPicker />} />
        <Route path="/management" element={<Management />} />
        <Route path="/lcd" element={<Lcd />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
