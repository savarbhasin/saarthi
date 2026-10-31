import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Served by FastAPI: the app under /app, the landing page at /, the slides at /deck. In
// dev, API calls go to the local backend and the pages live at /app/{landing,deck}.html.
export default defineConfig(({ mode }) => ({
  base: "/app/",
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: { input: { app: "index.html", landing: "landing.html", deck: "deck.html" } },
  },
  server: {
    port: 5173,
    proxy: { "/api": loadEnv(mode, ".", "").SAARTHI_API || "http://127.0.0.1:8091" },
  },
}));
