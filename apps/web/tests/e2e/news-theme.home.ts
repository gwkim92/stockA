import { expect, test } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
const api = 'http://127.0.0.1:18769';
test.beforeEach(async ({ request }) => { await request.post(`${api}/__scenario`, { data: { scenario: 'healthy' } }); });
for (const [path, name, id, first] of [
  ['/events', 'news', 'news-workspace', '[data-testid=news-inbox] > article'],
  ['/themes/semiconductor', 'theme', 'theme-workspace', '[data-testid=theme-companies] > article'],
]) {
  test(`${name} has accessible reading content and a reviewed production capture`, async ({ page }, info) => {
    const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
    await page.goto(path); const workspace = page.getByTestId(id);
    await expect(workspace.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.locator(first).first()).toBeVisible();
    expect((await page.locator(first).first().boundingBox())!.y).toBeLessThan(700);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]); expect(errors).toEqual([]);
    await page.screenshot({ path: info.outputPath(`signals-${name}-${info.project.name}.png`), fullPage: true, animations: 'disabled' });
    await page.screenshot({ path: info.outputPath(`signals-${name}-${info.project.name}-viewport.png`), animations: 'disabled' });
  });
}
test('literal page search and triage filters retain date, reload and history state', async ({ page }) => {
  await page.goto('/events?date=2024-11-01'); const inbox = page.getByTestId('news-inbox');
  await inbox.getByRole('textbox', { name: '뉴스 본문 검색' }).fill('AAPL');
  await expect(inbox.getByRole('article')).toHaveCount(1);
  await page.reload(); await expect(inbox.getByRole('textbox')).toHaveValue('AAPL');
  await inbox.getByRole('button', { name: /해석 미연결/ }).click();
  await expect(inbox).toContainText('이 페이지에서 조건에 맞는 기록이 없습니다');
  await page.goBack(); await expect(inbox.getByRole('article')).toHaveCount(1);
  await inbox.getByRole('button', { name: '선별 초기화' }).click();
  await expect(inbox.getByRole('article')).toHaveCount(4); await expect(page).toHaveURL(/date=2024-11-01/);
  await inbox.getByRole('button', { name: /차단·보류/ }).click();
  await expect(inbox.getByRole('article')).toHaveCount(1); await expect(inbox).toContainText('추천 입력 차단·보류');
});
test('next-page cursor is a real request and local filters never claim full-dataset search', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'paged' } });
  await page.goto('/events?date=2024-11-01&q=AAPL'); const inbox = page.getByTestId('news-inbox');
  await expect(inbox.getByRole('article')).toHaveCount(1); await expect(inbox).toContainText('수신 50개 기록');
  await inbox.getByRole('link', { name: '다음 페이지 →', exact: true }).click();
  await expect(page).toHaveURL(/cursor=/); await expect(inbox).toContainText('다음 페이지 AAPL 뉴스');
  await expect(inbox).toContainText('수신 2개 기록'); await expect(inbox.getByRole('textbox')).toHaveValue('AAPL');
  const requests: { path: string; query: string }[] = await (await request.get(`${api}/__requests`)).json();
  expect(requests.some(r => r.path === '/api/events' && r.query.includes('cursor='))).toBe(true);
  await inbox.getByRole('link', { name: '첫 페이지로', exact: true }).click();
  await expect(page).not.toHaveURL(/cursor=/); await expect(inbox).toContainText('수신 50개 기록');
});
test('applying server symbol/date criteria resets cursor and changes the backend request', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'paged' } });
  await page.goto('/events'); await page.getByRole('link', { name: '다음 페이지 →', exact: true }).click();
  await page.locator('summary').filter({ hasText: '종목·테마로 조회 범위 좁히기' }).click();
  await page.getByRole('textbox', { name: '조회 종목 코드' }).fill('AAPL');
  await page.getByLabel('기준일까지 조회').fill('2024-11-01');
  await page.getByRole('button', { name: '조회 적용' }).click();
  await expect(page).not.toHaveURL(/cursor=/); await expect(page).toHaveURL(/symbol=AAPL/);
  await expect(page.getByTestId('news-inbox').getByRole('article')).toHaveCount(2);
  const requests: { path: string; query: string }[] = await (await request.get(`${api}/__requests`)).json();
  const last = requests.filter(r => r.path === '/api/events').at(-1)!;
  expect(last.query).toContain('asOfDate=2024-11-01'); expect(last.query).toContain('symbol=AAPL'); expect(last.query).not.toContain('cursor=');
});
test('news to theme preserves the cutoff and opens a real connected company', async ({ page, request }) => {
  await page.goto('/events?date=2024-11-01');
  await page.getByTestId('news-inbox').getByRole('link', { name: '테마 검토 →', exact: true }).first().click();
  await expect(page).toHaveURL(/themes\/semiconductor\?date=2024-11-01/);
  await expect(page.getByTestId('theme-workspace')).toContainText('요청 기준일 2024-11-01');
  await page.getByTestId('theme-companies').getByRole('link', { name: '기업 분석 →', exact: true }).first().click();
  await expect(page).toHaveURL(/stocks\/AAPL$/); await expect(page.getByTestId('company-workspace')).toBeVisible();
  await page.goBack();
  await page.getByRole('link', { name: '이 테마의 뉴스 선별 →', exact: true }).click();
  await expect(page).toHaveURL(/theme=semiconductor/); await expect(page).toHaveURL(/date=2024-11-01/);
  const calls: { path: string; query: string; method: string }[] = await (await request.get(`${api}/__requests`)).json();
  expect(calls.some(r => r.path === '/api/themes/semiconductor' && r.query.includes('asOfDate=2024-11-01'))).toBe(true);
  expect(calls.some(r => r.path === '/api/events' && r.query.includes('themeKey=semiconductor'))).toBe(true);
  expect(calls.every(r => r.method === 'GET')).toBe(true);
});
test('news opens its exact interpretation and source', async ({ page }) => {
  await page.goto('/events');
  await page.getByTestId('news-inbox').getByRole('link', { name: '근거 해석 →', exact: true }).first().click();
  await expect(page).toHaveURL(/ai-evidence\/ai-evidence-1$/);
  await page.getByTestId('research-reader').getByRole('link', { name: '원천 문서 열기', exact: true }).click();
  await expect(page).toHaveURL(/source-documents\/source-document-1$/);
  await expect(page.getByTestId('source-excerpts')).toBeVisible();
});
test('theme company filters and normalized zero/missing features remain honest', async ({ page }) => {
  await page.goto('/themes/semiconductor?date=2024-11-01'); const companies = page.getByTestId('theme-companies');
  await companies.getByRole('button', { name: '투자 논리 미연결', exact: true }).click();
  await expect(companies.getByRole('article')).toHaveCount(1); await expect(companies).toContainText('MSFT');
  await page.reload(); await expect(companies.getByRole('button', { name: '투자 논리 미연결', exact: true })).toHaveAttribute('aria-pressed', 'true');
  await companies.getByRole('button', { name: '종목 조건 초기화' }).click();
  await companies.getByRole('textbox').fill('AAPL'); await expect(companies.getByRole('article')).toHaveCount(1);
  await expect(page.locator('#theme-features')).toContainText('0%'); await expect(page.locator('#theme-features')).toContainText('미측정');
  await companies.getByRole('link', { name: '투자 논리 →', exact: true }).click();
  await expect(page).toHaveURL(/theses\/thesis-1$/); await expect(page.getByTestId('research-reader')).toBeVisible();
});
test('duplicate history and source relationships remain visible without key collisions', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'duplicate' } });
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await page.goto('/themes/semiconductor');
  await expect(page.locator('#theme-history')).toContainText('동일 기준일 기록 중복');
  await expect(page.locator('#theme-news > article')).toHaveCount(3); expect(errors).toEqual([]);
});
for (const [scenario, path, expected] of [
  ['empty', '/events', '수신된 뉴스 목록이 비어 있습니다'],
  ['unknown', '/events', '추가 페이지 정보 미확인'],
  ['bad-paging', '/events', '추가 페이지 정보 미확인'],
  ['unknown', '/themes/semiconductor', '연결 기업 자료 미제공'],
  ['mismatch', '/themes/semiconductor', '요청 조건과 반환 자료를 대조해야 합니다'],
  ['all-down', '/events', '자료를 불러오지 못했습니다'],
  ['slow-body', '/events', '자료 응답이 지연되고 있습니다'],
]) {
  test(`${scenario} at ${path} is not a fake healthy or empty response`, async ({ page, request }) => {
    await request.post(`${api}/__scenario`, { data: { scenario } }); await page.goto(path);
    await expect(page.locator('main')).toContainText(expected);
    await expect(page.locator('main')).not.toContainText('private-fixture-error');
    if (scenario === 'bad-paging') await expect(page.getByRole('link', { name: '다음 페이지 →', exact: true })).toHaveCount(0);
  });
}
test('invalid and duplicate dates are refused before the backend call', async ({ page, request }) => {
  await page.goto('/events?date=2026-02-30'); await expect(page.locator('main')).toContainText('조회 조건을 확인해 주세요');
  await page.goto('/themes/semiconductor?date=2024-11-01&date=2024-12-01');
  await expect(page.locator('main')).toContainText('조회 조건을 확인해 주세요');
  const calls = await (await request.get(`${api}/__requests`)).json(); expect(calls).toHaveLength(0);
});
test('stored markup stays literal rather than becoming executable content', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'literal' } }); await page.goto('/events');
  await expect(page.getByTestId('news-inbox')).toContainText('<script>window.newsInjection=true</script>');
  expect(await page.evaluate(() => (window as unknown as { newsInjection?: boolean }).newsInjection)).toBeUndefined();
});
