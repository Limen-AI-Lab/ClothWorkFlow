import path from 'node:path'
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const projectRoot = path.resolve(__dirname, '../..')
  const all = loadEnv(mode, projectRoot, '')
  const geminiKey =
    all.GEMINI_API_KEY ||
    all.GOOGLE_API_KEY ||
    all.VITE_GEMINI_API_KEY ||
    ''
  const imageModel =
    all.VITE_GEMINI_IMAGE_MODEL || all.GEMINI_IMAGE_MODEL || ''

  return {
    plugins: [react()],
    /** 与根目录 .env 共用 GEMINI_API_KEY，无需再复制一份 VITE_ 变量 */
    envDir: projectRoot,
    define: {
      'import.meta.env.VITE_GEMINI_API_KEY': JSON.stringify(geminiKey),
      ...(imageModel
        ? {
            'import.meta.env.VITE_GEMINI_IMAGE_MODEL':
              JSON.stringify(imageModel),
          }
        : {}),
    },
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'antd-vendor': ['antd', '@ant-design/icons', '@ant-design/charts'],
          },
        },
      },
    },
  }
})
