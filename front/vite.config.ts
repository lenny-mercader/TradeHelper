import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Backend address seen from the Vite dev server (overridden in docker-compose).
const backendUrl = process.env.BACKEND_URL ?? 'http://localhost:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    strictPort: true,
    // Windows bind mounts don't forward file events into Linux containers.
    watch: process.env.VITE_USE_POLLING === 'true' ? { usePolling: true } : undefined,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
      },
    },
  },
})
