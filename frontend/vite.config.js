import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Bind to all interfaces so the container is reachable from the host.
    // Removes the need for the --host CLI flag in the Docker CMD.
    host: true,
    port: 5173,
    // Dev-mode proxy — forwards API and WebSocket calls to the operator so
    // the browser never hits a CORS wall during local development.
    // In production the nginx reverse proxy in Dockerfile.frontend handles this.
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
