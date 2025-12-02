import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        host: 'localhost',
        port: 5173,
        strictPort: false,
    },
    preview: {
        host: 'localhost',
        port: 4173,
    },
})