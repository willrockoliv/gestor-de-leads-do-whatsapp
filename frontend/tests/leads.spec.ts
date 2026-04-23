import { test, expect } from '@playwright/test';

// Helper para login (ajuste conforme necessário)
async function login(page) {
  // Usa baseURL do Playwright config se disponível, senão fallback para localhost:3000
  const base = process.env.PLAYWRIGHT_TEST_BASE_URL || process.env.BASE_URL || 'http://localhost:3000';
  await page.goto(`${base}/login`);
  await page.fill('input[type="email"]', 'teste@teste.com');
  await page.fill('input[type="password"]', '123456');
  await page.click('button[type="submit"]');
  await page.waitForURL(`${base}/dashboard`);
}

test.describe('Página de Leads - Visual e Funcional', () => {
  test.beforeEach(async ({ page }) => {
    test.setTimeout(300000);
    await login(page);
    const base = process.env.PLAYWRIGHT_TEST_BASE_URL || process.env.BASE_URL || 'http://localhost:3000';
    await page.goto(`${base}/leads`);
  });

  test('Deve exibir título, filtros, tabela e ações', async ({ page }) => {
    test.setTimeout(300000);
    // Garante que o h1 de Leads está visível
    await expect(page.locator('h1')).toHaveText(/leads/i);
    await expect(page.getByPlaceholder('Buscar por nome ou telefone...')).toBeVisible();
    await expect(page.getByText('Etapa')).toBeVisible();
    await expect(page.getByText(/Temperatura/)).toBeVisible();
    await expect(page.getByRole('table')).toBeVisible();
    // Checa pelo menos uma linha de lead (mock ou real)
    const rows = await page.locator('table tbody tr');
    expect(await rows.count()).toBeGreaterThan(0);
  });

  test('Deve alternar filtro de etapa e buscar leads', async ({ page }) => {
    test.setTimeout(300000);
    await page.getByPlaceholder('Buscar por nome ou telefone...').fill('');
    await page.getByText('Etapa').click();
    // Seleciona a primeira etapa disponível
    const items = page.locator('[role="option"]');
    if (await items.count() > 1) {
      await items.nth(1).click();
      await expect(page.getByRole('table')).toBeVisible();
    }
  });

  test('Deve acionar análise de lead e exibir loading', async ({ page }) => {
    test.setTimeout(300000);
    // Clica no primeiro botão de analisar
    const analyzeBtn = page.locator('button[title="Analisar"]').first();
    await analyzeBtn.click();
    // Deve mostrar loading/spinner
    await expect(analyzeBtn.locator('svg.animate-spin')).toBeVisible();
  });

  test('Deve abrir e cancelar dialog de status', async ({ page }) => {
    test.setTimeout(300000);
    const convertBtn = page.locator('button[title="Marcar como convertido"]').first();
    await convertBtn.click();
    await expect(page.getByText(/Confirmar alteração de status/i)).toBeVisible();
    await page.getByRole('button', { name: /cancelar/i }).click();
    await expect(page.getByText(/Confirmar alteração de status/i)).not.toBeVisible();
  });
});
