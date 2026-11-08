import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => {
  const demo = mode === 'demo'
  return {
    plugins: [react()],
    base: demo ? './' : '/',
    server: {
      port: 5173,
      proxy: {
        '/api': { target: 'http://127.0.0.1:8010', changeOrigin: true },
        '/ws': { target: 'ws://127.0.0.1:8010', ws: true },
      },
    },
    ...(demo
      ? {
          build: {
            outDir: '../docs/app',
            emptyOutDir: true,
            rollupOptions: { input: 'demo.html' },
          },
        }
      : {}),
  }
})
