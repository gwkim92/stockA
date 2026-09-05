import { test, expect } from '@playwright/test';
test.beforeEach(async ({ request }) => { await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario: 'healthy' } }); });

test('complete stored fund analysis remains reachable without company model substitution', async ({ page }) => {
  await page.goto('/stocks/SPY/details');
  const report = page.getByTestId('company-full-analysis');
  await expect(report).toContainText('추적'); await expect(report).toContainText('비용');
  await expect(report.locator('#stock-financial-model')).toHaveCount(0);
});
test('reported financial ratios remain consistent between company summary and detail', async ({ page }) => {
  await page.goto('/stocks/AAPL');
  await expect(page.locator('#company-analysis')).toContainText('매출 성장률');
  await expect(page.locator('#company-analysis')).toContainText('12%');
  await page.getByRole('link', { name: '전문 분석 전체 보기 →', exact: true }).click();
  await expect(page.locator('#stock-financial-model')).toContainText('매출 성장률');
  await expect(page.locator('#stock-financial-model')).toContainText('12%');
});

for (const [path, selector] of [['/stocks/AAPL', '#company-case > p'], ['/ai-evidence/ai-evidence-1', '#evidence-interpretation > div']]) {
  test(`reading and primary source navigation remain early at ${path}`, async ({ page }) => {
    await page.goto(path);
    expect((await page.locator(selector).first().boundingBox())!.y).toBeLessThan(700);
    if (path.includes('ai-evidence')) expect((await page.getByRole('link', { name: '원천 문서 열기', exact: true }).boundingBox())!.y).toBeLessThan(700);
  });
}
