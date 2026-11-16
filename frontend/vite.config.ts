import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Carrega variáveis tanto do diretório frontend quanto da raiz do repositório
  const envFrontend = loadEnv(mode, process.cwd(), '')
  const envRaiz = loadEnv(mode, path.resolve(process.cwd(), '..'), '')
  const env = { ...envRaiz, ...envFrontend }
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
