import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/list-rfps': 'http://localhost:8000',
      '/ingest/drive': 'http://localhost:8000',
      '/analyze': 'http://localhost:8000',
      '/write_proposal': 'http://localhost:8000',
      '/upload/rfp': 'http://localhost:8000'
    }
  }
})
