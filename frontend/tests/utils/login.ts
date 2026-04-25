import { Page } from '@playwright/test';

export async function login(page: Page) {
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'teste@teste.com');
  await page.fill('input[type="password"]', '123456');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard');
  // Aguarda o token ser salvo no localStorage
  await page.waitForFunction(() => !!localStorage.getItem('token'), null, { timeout: 10000 });
  const token = await page.evaluate(() => localStorage.getItem('token'));
}
