
// Este teste depende de:
// 1. Seed com leads que possuem mensagens (ver frontend/tests/scripts/seed_e2e.py)
// 2. Mock da resposta do endpoint de análise (feito via page.route)
// Assim, o teste valida apenas o feedback visual (loading/spinner) ao acionar análise, sem depender de backend real ou LLM.
import { test, expect } from '@playwright/test';
import { login } from './utils/login';

test.describe('Página de Leads - Visual e Funcional', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(20000);
    // Faz login (aguarda /dashboard)
    await login(page);
    // Aguarda um pequeno delay para garantir que o contexto React hidrate o token
    await page.waitForTimeout(300);
    // Clica no link "Leads" no sidebar
    await page.getByRole('link', { name: 'Leads', exact: true }).click();
    // Aguarda navegação
    await page.waitForLoadState('networkidle');
    // Garante que não foi redirecionado de volta para login
    expect(page.url()).not.toContain('/login');
  });

  test('Deve exibir título, filtros, tabela e ações', async ({ page }) => {
    test.setTimeout(300000);
    try {
      // Aguarda o carregamento terminar (skeleton sumir)
      await page.waitForSelector('h1', { timeout: 10000 });
      await expect(page.locator('h1')).toHaveText(/leads/i, { timeout: 4000 });
      await expect(page.getByPlaceholder('Buscar por nome ou telefone...')).toBeVisible({ timeout: 2000 });
      await expect(page.getByText('Etapa')).toBeVisible({ timeout: 2000 });
      await expect(page.getByRole('columnheader', { name: 'Temperatura' })).toBeVisible({ timeout: 2000 });
      await expect(page.getByRole('table')).toBeVisible({ timeout: 2000 });
      // Checa pelo menos uma linha de lead (mock ou real)
      const rows = await page.locator('table tbody tr');
      expect(await rows.count()).toBeGreaterThan(0);
    } catch (e) {
      const html = await page.content();
      console.log('HTML da página de leads ao falhar:', html);
      throw e;
    }
  });

  test('Deve alternar filtro de etapa e buscar leads', async ({ page }) => {
    test.setTimeout(20000);
    await page.getByPlaceholder('Buscar por nome ou telefone...').fill('');
    await page.getByText('Etapa').click();
    // Seleciona a primeira etapa disponível
    const items = page.locator('[role="option"]');
    if (await items.count() > 1) {
      await items.nth(1).click();
      await expect(page.getByRole('table')).toBeVisible({ timeout: 2000 });
    }
  });

  test('Deve acionar análise de lead e exibir loading', async ({ page }) => {
    test.setTimeout(20000);
    // Mock da resposta do backend/LLM para análise
    await page.route('**/api/analysis', async route => {
      // Simula um pequeno delay para o loading aparecer
      await new Promise(r => setTimeout(r, 500));
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ result: 'mocked analysis' }),
      });
    });
    // Clica no primeiro botão de analisar
    const analyzeBtn = page.locator('button[title="Analisar"]').first();
    await analyzeBtn.click();
    // Deve mostrar loading/spinner
    await expect(analyzeBtn.locator('svg.animate-spin')).toBeVisible({ timeout: 2000 });
  });

  test('Deve abrir e cancelar dialog de status', async ({ page }) => {
    test.setTimeout(20000);
    const convertBtn = page.locator('button[title="Marcar como convertido"]').first();
    await convertBtn.click();
    await expect(page.getByText(/Confirmar alteração de status/i)).toBeVisible({ timeout: 2000 });
    await page.getByRole('button', { name: /cancelar/i }).click();
    await expect(page.getByText(/Confirmar alteração de status/i)).not.toBeVisible({ timeout: 2000 });
  });
});
