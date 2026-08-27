import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const apiProxyTarget = env.VITE_DEV_API_PROXY_TARGET || 'http://localhost:8787'

  return {
    plugins: [vue()],
    server: { port: 5173, proxy: { '/api': apiProxyTarget } },
  }
})
