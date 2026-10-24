import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@vitejs/plugin-react' // not needed
import tailwindcss from '@tailwindcss/vite'

// Build for GitHub Pages from /docs
export default defineConfig({
  base: './',
  plugins: [react(), tailwindcss()],
  server: { host: '127.0.0.1' },
  build: {
    outDir: '../docs',
    emptyOutDir: true,
    assetsDir: 'assets'
  },
  test: { environment: 'jsdom' }
})
