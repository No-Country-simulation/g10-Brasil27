import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiKey = (env.MEDIFLOW_API_KEY || process.env.MEDIFLOW_API_KEY || '').trim()

  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: env.MEDIFLOW_API_URL || 'http://localhost:8000',
          changeOrigin: true,
          headers: apiKey ? { 'X-API-Key': apiKey } : {}
        }
      }
    }
  }
})
