import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Force new bundle generation - disable rollup cache
    rollupOptions: {
      output: {
        // Add timestamp to force cache invalidation
        assetFileNames: 'assets/[name]-[hash]-v2.[ext]',
        chunkFileNames: 'assets/[name]-[hash]-v2.js',
        entryFileNames: 'assets/[name]-[hash]-v2.js',
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
