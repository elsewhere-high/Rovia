import { expect, test as base } from '@playwright/test'

export const test = base.extend({
  page: async ({ page }, use) => {
    const login = await page.request.post('/api/v1/auth/login', {
      data: {
        email: process.env.ROVIA_E2E_EMAIL || 'ui-test@example.test',
        password: process.env.ROVIA_E2E_PASSWORD || 'local-browser-test-password',
      },
    })
    expect(login.status(), 'Browser tests require a real authenticated session').toBe(200)
    await use(page)
  },
})

export { expect } from '@playwright/test'
