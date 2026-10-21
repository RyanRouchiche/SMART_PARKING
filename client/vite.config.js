import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const django = env.DJANGO_URL || "http://127.0.0.1:8000";

  return {
    plugins: [react()],
    server: {
      host: true,
      proxy: {
        "/api": django,
        "/admin": django,
        "/static": django,
        "/ws": { target: django.replace(/^http/, "ws"), ws: true },
      },
    },
  };
});
