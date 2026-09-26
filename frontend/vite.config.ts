import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  envDir: '..',
  plugins: [
    vue({
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'model-viewer',
        },
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.ROVIA_API_TARGET || 'http://localhost:8000',
      '/health': process.env.ROVIA_API_TARGET || 'http://localhost:8000',
    },
  },
})
