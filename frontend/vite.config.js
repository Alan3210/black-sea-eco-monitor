import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    host: '127.0.0.1',
    port: 5173,
    proxy: {
      '/monitor': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
      '/ocean': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
});
