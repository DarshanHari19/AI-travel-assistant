import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Force v4 bundle - FINAL attempt to bypass cache
    rollupOptions: {
      output: {
        // v4 - includes Railway URL hardcoded
        assetFileNames: 'assets/[name]-[hash]-v4-final.[ext]',
        chunkFileNames: 'assets/[name]-[hash]-v4-final.js',
        entryFileNames: 'assets/[name]-[hash]-v4-final.js',
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
