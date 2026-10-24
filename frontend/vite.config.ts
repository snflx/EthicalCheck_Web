import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Use base path for GitHub Pages deployment
export default defineConfig({
  base: '/ethicalcheck/',
  plugins: [react(), tailwindcss()],
  server: { host: '127.0.0.1' },
  build: { outDir: 'dist', assetsDir: 'assets' },
  test: { environment: 'jsdom' }
})
