import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/index.js";
import { usePresence } from "../features/parking/index.js";
import { ZonesProvider } from "../features/detection/index.js";

export default function RequireAuth() {
  const { user } = useAuth();
  usePresence(Boolean(user));

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
