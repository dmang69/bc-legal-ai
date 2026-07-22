import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// Shared UI for Tauri shells + web portal / PWA.
// Do not put secrets or matter data in the client bundle.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["favicon.svg"],
      manifest: {
        name: "BC Legal AI Portal",
        short_name: "BC Legal AI",
        description:
          "BC Legal AI Associate — supervised legal research and drafting support. Not a lawyer.",
        theme_color: "#1a2332",
        background_color: "#0f1419",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
      workbox: {
        // Never cache API/matter payloads offline as full matter dumps
        navigateFallback: "/index.html",
        runtimeCaching: [
          {
            urlPattern: /\/v1\//,
            handler: "NetworkOnly",
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    strictPort: true,
  },
  clearScreen: false,
  envPrefix: ["VITE_", "TAURI_"],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    target: process.env.TAURI_ENV_PLATFORM === "windows" ? "chrome105" : "safari14",
  },
});
