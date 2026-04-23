import { test, expect } from '@playwright/test';

// Teste visual e funcional do dashboard

async function login(page) {
  await page.goto('http://localhost:3000/login');
  await page.fill('input[type="email"]', 'teste@teste.com');
  await page.fill('input[type="password"]', '123456');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/dashboard');
  // Aguarda o token ser salvo no localStorage
  await page.waitForFunction(() => !!localStorage.getItem('token'), null, { timeout: 10000 });
  const token = await page.evaluate(() => localStorage.getItem('token'));
  console.log('Token JWT após login:', token);
}

test.describe('Dashboard visual e funcional', () => {
  test('Deve exibir hero, cards, kanban e badges corretamente', async ({ page }) => {
    test.setTimeout(300000);
    await login(page);
    // Hero
    await expect(page.getByRole('heading', { name: /painel de leads/i })).toBeVisible();
    await expect(page.getByText(/acompanh/i)).toBeVisible();
    // Aguarda o sumiço do loader
    await expect(page.getByText('Carregando...')).toBeHidden({ timeout: 120000 });
    // Cards
    try {
      await expect(page.getByText('Leads Ativos', { exact: false })).toBeVisible({ timeout: 60000 });
      await expect(page.getByText('Convertidos', { exact: false })).toBeVisible({ timeout: 60000 });
      await expect(page.getByText('Perdidos', { exact: false })).toBeVisible({ timeout: 60000 });
      await expect(page.getByText('Temperatura Média', { exact: false })).toBeVisible({ timeout: 60000 });
    } catch (e) {
      const html = await page.content();
      console.log('HTML do dashboard ao falhar:', html);
      throw e;
    }
    // Kanban
    await expect(page.getByText(/funil de vendas/i)).toBeVisible();
    // Badge de temperatura
    await expect(page.locator('.bg-teal-50, .dark\\:bg-teal-500\\/10')).toBeVisible({ timeout: 5000 });
  });

  test('Deve alternar entre light e dark mode', async ({ page }) => {
    test.setTimeout(300000);
    await login(page);
    // Toggle para dark
    await page.locator('button[aria-label*="tema"]').first().click();
    await page.waitForTimeout(1500); // Aguarda para aplicação do tema
    // Verifica se body OU html tem classe dark OU data-theme=dark
    const hasDarkClass = await page.evaluate(() => {
      return (
        document.body.classList.contains('dark') ||
        document.documentElement.classList.contains('dark') ||
        document.body.getAttribute('data-theme') === 'dark' ||
        document.documentElement.getAttribute('data-theme') === 'dark'
      );
    });
    expect(hasDarkClass).toBe(true);
    // Toggle para light
    await page.locator('button[aria-label*="tema"]').first().click();
    await page.waitForTimeout(1500);
    const hasDarkClassAfter = await page.evaluate(() => {
      return (
        document.body.classList.contains('dark') ||
        document.documentElement.classList.contains('dark') ||
        document.body.getAttribute('data-theme') === 'dark' ||
        document.documentElement.getAttribute('data-theme') === 'dark'
      );
    });
    expect(hasDarkClassAfter).toBe(false);
  });
});
