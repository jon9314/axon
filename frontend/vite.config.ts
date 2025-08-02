import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import type { ManifestOptions } from 'vite-plugin-pwa'
import manifest from './manifest.json' assert { type: 'json' }

const pwaManifest = manifest as Partial<ManifestOptions>

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      strategies: 'injectManifest',
      srcDir: '.',
      filename: 'serviceWorker.ts',
      injectManifest: {
        injectionPoint: undefined,
      },
      manifest: pwaManifest,
    }),
  ],
})
