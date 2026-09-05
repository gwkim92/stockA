import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
test.beforeEach(async ({ request }) => { await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario: 'healthy' } }); });
for (const [path, name, id] of [['/stocks/AAPL', 'company', 'company-workspace'], ['/ai-evidence/ai-evidence-1', 'evidence', 'research-reader']]) {
  test(`${name} renders the production workspace with accessible readable content`, async ({ page }, info) => {
    const errors: string[] = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(path); const workspace = page.getByTestId(id);
    await expect(workspace.getByRole('heading', { level: 1 })).toBeVisible();
    const first = workspace.locator(name === 'company' ? '#company-case > p' : '#evidence-interpretation > div').first();
    expect((await first.boundingBox())!.y).toBeLessThan(info.project.name === 'mobile' ? 900 : 750);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]); expect(errors).toEqual([]);
    await page.screenshot({ path: info.outputPath(`${name}-${info.project.name}.png`), fullPage: true, animations: 'disabled' });
    await page.screenshot({ path: info.outputPath(`${name}-${info.project.name}-viewport.png`), animations: 'disabled' });
  });
}
test('price observation controls do not relabel sparse history as daily change', async ({ page }) => {
  await page.goto('/stocks/AAPL'); const chart = page.getByTestId('company-price-chart');
  await expect(page.getByTestId('company-workspace').locator('dl').first()).toContainText('보고된 1일 변화');
  await expect(chart).toContainText('29/30개 측정');
  await chart.getByRole('button', { name: '수신 전체', exact: true }).click(); await expect(chart).toContainText('44/45개 측정');
  await chart.locator('summary').click(); await expect(chart.getByRole('table')).toContainText('미측정');
  const path = await chart.locator('svg path').getAttribute('d'); expect(path?.split('M')).toHaveLength(3);
});
for (const scenario of ['context-down', 'context-wrong', 'context-slow']) {
  test(`${scenario} cannot erase primary research or attach an unrelated thesis`, async ({ page, request }) => {
    await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario } });
    await page.goto('/stocks/AAPL', { waitUntil: 'domcontentloaded' });
    const view = page.getByTestId('company-workspace');
    await expect(view.locator('#company-case')).toContainText('서비스의 반복 매출');
    await expect(view.locator('#company-context')).toContainText('추가 시장 문맥을 불러오지 못했습니다');
    await expect(view).not.toContainText('unrelated-first-thesis'); await expect(view).not.toContainText('optional-private-error');
    await expect(view.getByRole('link', { name: '투자 논리 열기', exact: true })).toHaveAttribute('href', '/theses/thesis-1');
  });
}
test('company facts remain unknown instead of fabricated prices or non-holdings', async ({ page, request }) => {
  await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario: 'stock-unknown' } });
  await page.goto('/stocks/AAPL'); const view = page.getByTestId('company-workspace');
  await expect(view.locator('dl').first()).toContainText('미확인');
  await expect(view).toContainText('가격 관측 목록 미제공'); await expect(view).not.toContainText('보유 수량 없음');
});
test('fund primary page shows composition rather than company target values', async ({ page }) => {
  await page.goto('/stocks/SPY'); const view = page.getByTestId('company-workspace');
  await expect(view).toContainText('보유 구성과 비용'); await expect(view).toContainText('S&P 500');
  await expect(view).toContainText('0.09%'); await expect(view).not.toContainText('중앙 추정 가치');
});
test('company to interpretation to original source and back is actual navigation', async ({ page, request }) => {
  await page.goto('/stocks/AAPL'); await page.getByRole('link', { name: '근거 해석 열기 →', exact: true }).click();
  await expect(page).toHaveURL(/ai-evidence\/ai-evidence-1$/);
  await page.getByTestId('research-reader').getByRole('link', { name: '원천 문서 열기', exact: true }).click();
  await expect(page).toHaveURL(/source-documents\/source-document-1$/); await expect(page.getByTestId('source-excerpts')).toBeVisible();
  const requests = await (await request.get('http://127.0.0.1:18768/__requests')).json();
  expect(requests.every((r: { method: string }) => r.method === 'GET')).toBe(true);
});
test('retained professional report still opens and primary route does not prefetch it', async ({ page, request }) => {
  await page.goto('/stocks/AAPL'); const link = page.getByRole('link', { name: '전문 분석 전체 보기 →', exact: true });
  await link.hover(); const before = await (await request.get('http://127.0.0.1:18768/__requests')).json();
  expect(before.filter((r: { path: string }) => r.path === '/api/stocks/AAPL')).toHaveLength(1);
  await link.click(); await expect(page).toHaveURL(/stocks\/AAPL\/details$/);
  await expect(page.getByTestId('company-full-analysis')).toContainText('재무제표 모델');
  await page.getByRole('link', { name: '← 기업 리서치로 돌아가기', exact: true }).click(); await expect(page).toHaveURL(/stocks\/AAPL$/);
});
test('exact extracted field links lead to the actual referenced chunk', async ({ page }) => {
  await page.goto('/ai-evidence/ai-evidence-1'); const fields = page.getByTestId('evidence-fields');
  const first = fields.getByRole('link', { name: '근거 발췌 확인 →', exact: true }).first();
  await expect(first).toHaveAttribute('href', '#evidence-chunk-1'); await first.click();
  await expect(page.locator('#evidence-chunk-1')).toBeInViewport();
  await expect(page.locator('#evidence-sources')).toContainText('Customer retention and recurring revenue');
  await expect(page.getByTestId('research-reader')).toContainText('저장된 한국어 요약이 없습니다');
});
test('rejected evidence retains uncertainty and cannot appear approved', async ({ page, request }) => {
  await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario: 'blocked' } });
  await page.goto('/ai-evidence/ai-evidence-1'); const view = page.getByTestId('research-reader');
  await expect(view).toContainText('추천 입력 제외 · 차단 기록'); await expect(view).toContainText('인과관계는 확인되지 않았습니다');
  await expect(view).toContainText('출처가 부족하여 입력에서 제외');
});
for (const [scenario, expected] of [['chunk-missing', '대응하는 발췌를 수신하지 못했습니다'], ['cluster', '묶음 이벤트 둘'], ['source-mismatch', '원천 링크를 보류했습니다'], ['evidence-wrong', '요청한 자료와 응답을 대조해야 합니다'], ['all-down', '자료를 불러오지 못했습니다']]) {
  test(`${scenario} preserves the interpretation boundary`, async ({ page, request }) => {
    await request.post('http://127.0.0.1:18768/__scenario', { data: { scenario } }); await page.goto('/ai-evidence/ai-evidence-1');
    await expect(page.locator('main')).toContainText(expected); await expect(page.locator('main')).not.toContainText('private-error-must-not-render');
  });
}
