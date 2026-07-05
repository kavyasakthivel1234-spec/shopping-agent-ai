import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/**
 * vite.config.js
 * --------------
 * The proxy block forwards ALL /api/* requests from the Vite dev server
 * (port 5173) to the FastAPI backend (port 8000).
 *
 * This means the frontend uses relative paths like "/api/auth/signup"
 * and Vite transparently rewrites them to "http://localhost:8000/api/auth/signup".
 *
 * No CORS issues, no hardcoded ports in frontend code.
 */
export default defineConfig({
  plugins: [react()],

  server: {
    port: 5173,
    proxy: {
      // Every request starting with /api is forwarded to FastAPI
      "/api": {
        target:       "http://localhost:8000",
        changeOrigin: true,   // rewrites the Host header to match the target
        secure:       false,  // allow self-signed certs in dev if needed
      },
    },
  },

  build: {
    outDir:     "dist",
    sourcemap:  false,
  },
});
