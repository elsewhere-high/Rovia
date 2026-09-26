import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  // The plan page mounts a model-viewer and a large map canvas.  Running two
  // browser workers concurrently can starve the browser's rendering queue and
  // make an otherwise healthy page miss Playwright's navigation timeout.  A
  // single worker keeps the acceptance suite deterministic; it still covers
  // every configured viewport and browser.
  workers: 1,
  use: {
    baseURL: process.env.ROVIA_E2E_BASE_URL || 'http://127.0.0.1:5174',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'desktop-1366',
      testIgnore: '**/firefox-compat.spec.ts',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1366, height: 768 } },
    },
    {
      name: 'desktop-1920',
      testIgnore: '**/firefox-compat.spec.ts',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1920, height: 1080 } },
    },
    {
      name: 'firefox-3d',
      testMatch: '**/firefox-compat.spec.ts',
      use: { ...devices['Desktop Firefox'], viewport: { width: 1366, height: 768 } },
    },
  ],
  webServer: process.env.ROVIA_E2E_BASE_URL ? undefined : [
    {
      command: 'conda run --no-capture-output -n rovia python ../scripts/e2e_backend.py',
      url: 'http://127.0.0.1:8765/health',
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort',
      url: 'http://127.0.0.1:5174',
      reuseExistingServer: false,
      env: { ROVIA_API_TARGET: 'http://127.0.0.1:8765', VITE_API_BASE_URL: '', VITE_AMAP_JSAPI_KEY: '', VITE_AMAP_SECURITY_JS_CODE: '' },
    },
  ],
})
