import { expect, test } from '@playwright/test';
const api = 'http://127.0.0.1:18769';
test.beforeEach(async ({ request }) => { await request.post(`${api}/__scenario`, { data: { scenario: 'healthy' } }); });

test('first news source action is usable above the mobile dock without hiding context', async ({ page }, info) => {
  await page.goto('/events');
  const source = page.getByTestId('news-inbox').getByRole('article').first().getByRole('link', { name: '원천 문서 →', exact: true });
  await expect(source).toBeVisible();
  const bounds = (await source.boundingBox())!;
  const dock = info.project.name === 'mobile' ? await page.getByRole('navigation', { name: '모바일 주요 메뉴', exact: true }).boundingBox() : null;
  expect(bounds.y + bounds.height).toBeLessThan(dock?.y ?? page.viewportSize()!.height);
  await expect(page.getByTestId('news-inbox')).toContainText('현재 페이지에만 적용');
  await expect(page.getByTestId('news-workspace')).toContainText('UTC');
  await page.getByRole('link', { name: '테마 사이클 →', exact: true }).focus();
  await expect(page.getByRole('link', { name: '테마 사이클 →', exact: true })).toBeFocused();
});

test('a server-side symbol mismatch is not displayed as matching news', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'mismatch' } });
  await page.goto('/events?date=2024-11-01&symbol=AAPL');
  await expect(page.getByTestId('news-workspace')).toContainText('요청 조건과 반환 자료를 대조해야 합니다');
  await expect(page.getByTestId('news-inbox')).toHaveCount(0);
});

test('retry restores the requested date and local filter rather than switching to today', async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'all-down' } });
  await page.goto('/events?date=2024-11-01&q=AAPL');
  await expect(page.getByTestId('news-workspace')).toContainText('자료를 불러오지 못했습니다');
  await request.post(`${api}/__scenario`, { data: { scenario: 'healthy' } });
  await page.getByRole('link', { name: '다시 조회', exact: true }).click();
  await expect(page).toHaveURL(/date=2024-11-01/);
  await expect(page.getByTestId('news-inbox').getByRole('textbox')).toHaveValue('AAPL');
  await expect(page.getByTestId('news-inbox').getByRole('article')).toHaveCount(1);
  const requests: { path: string; query: string }[] = await (await request.get(`${api}/__requests`)).json();
  expect(requests.some(row => row.path === '/api/events' && row.query.includes('asOfDate=2024-11-01'))).toBe(true);
});
