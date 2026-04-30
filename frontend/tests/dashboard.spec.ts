import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test.describe('Dashboard visual e funcional', () => {
  test('Deve exibir hero, cards e kanban corretamente', async ({ page }) => {
    test.setTimeout(20000);
    await login(page);
    // Hero
    await expect(page.getByRole('heading', { name: /painel de leads/i })).toBeVisible();
    await expect(page.getByText(/acompanh/i)).toBeVisible();
    // Aguarda o sumiço do loader
    await expect(page.getByText('Carregando...')).toBeHidden({ timeout: 10000 });
    // Cards
    try {
      await expect(page.getByText('Leads Ativos', { exact: false })).toBeVisible({ timeout: 5000 });
      await expect(page.getByText('Convertidos', { exact: false })).toBeVisible({ timeout: 5000 });
      await expect(page.getByText('Perdidos', { exact: false })).toBeVisible({ timeout: 5000 });
      await expect(page.getByText('Temperatura Média', { exact: false })).toBeVisible({ timeout: 5000 });
    } catch (e) {
      const html = await page.content();
      console.log('HTML do dashboard ao falhar:', html);
      throw e;
    }
    // Kanban
    await expect(page.getByText(/funil de vendas/i)).toBeVisible();
  });

  test('Deve exibir badge quente no dashboard', async ({ page }) => {
    test.setTimeout(20000);
    await login(page);
    const badgeQuente = page.locator('span.group\\/badge', { hasText: 'Quente' });
    await expect(badgeQuente).toBeVisible({ timeout: 2000 });
    // Confere classes RFC (light e dark)
    await expect(badgeQuente).toHaveClass(/bg-teal-50/);
    await expect(badgeQuente).toHaveClass(/dark:bg-teal-500\/10/);
  });

  test('Deve exibir badge morno no dashboard', async ({ page }) => {
    test.setTimeout(20000);
    await login(page);
      const badgeMorno = page.locator('span.group\\/badge', { hasText: 'Morno' });
      await expect(badgeMorno).toBeVisible({ timeout: 2000 });
      // Confere classes RFC (light e dark)
      await expect(badgeMorno).toHaveClass(/bg-blue-50/);
      await expect(badgeMorno).toHaveClass(/dark:bg-blue-500\/10/);
  });

  test('Deve exibir badge frio no dashboard', async ({ page }) => {
    test.setTimeout(20000);
    await login(page);
      const badgeFrio = page.locator('span.group\\/badge', { hasText: 'Frio' });
      await expect(badgeFrio).toBeVisible({ timeout: 2000 });
      // Confere classes RFC (light e dark)
      await expect(badgeFrio).toHaveClass(/bg-slate-100/);
      await expect(badgeFrio).toHaveClass(/dark:bg-slate-800\/50/);
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
