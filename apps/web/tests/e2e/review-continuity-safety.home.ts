import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
const api = 'http://127.0.0.1:18770';
const key = 'stocka:company-review:v1:AAPL:instrument-aapl';
const route = '/stocks/AAPL/review?savedInstrument=instrument-aapl';
test.beforeEach(async ({ page, request }) => {
  await request.post(`${api}/__scenario`, { data: { scenario: 'healthy' } });
  await page.goto('/stocks/AAPL/review');
  await page.getByLabel('내 판단과 근거', { exact: true }).fill('검토함에서 처음 읽은 판단');
  await page.getByRole('button', { name: '이 브라우저에 저장', exact: true }).click();
  await expect(page.getByTestId('review-draft')).toContainText('이 브라우저에 저장했습니다');
  await page.goto(route);
  await expect(page.getByTestId('saved-review-comparison')).toContainText('검토함에서 처음 읽은 판단');
});

test('failed comparison reload after external deletion retains dirty text and export without recreating storage', async ({ page, context }) => {
  await page.getByLabel('내 판단과 근거', { exact: true }).fill('삭제 후에도 남아야 하는 미저장 검토');
  const other = await context.newPage(); await other.goto('/research-notes');
  await other.evaluate(key => localStorage.removeItem(key), key);
  await expect(page.getByTestId('review-draft')).toContainText('다른 탭에서 초안이 변경');
  await page.getByRole('button', { name: '선택한 저장 메모 다시 읽기', exact: true }).click();
  await expect(page.getByTestId('saved-review-comparison')).toContainText('이미 열어 작성 중인 편집기는 보존했습니다');
  await expect(page.getByLabel('내 판단과 근거', { exact: true })).toHaveValue('삭제 후에도 남아야 하는 미저장 검토');
  await expect(page.getByRole('button', { name: '이 브라우저에 저장', exact: true })).toBeDisabled();
  const waiting = page.waitForEvent('download');
  await page.getByRole('button', { name: '검토 노트 내보내기', exact: true }).click();
  expect(readFileSync((await (await waiting).path())!, 'utf8')).toContain('삭제 후에도 남아야 하는 미저장 검토');
  expect(await page.evaluate(key => localStorage.getItem(key), key)).toBeNull();
  await other.close();
});

test('same-tab saves update the editor but the read-only baseline changes only on explicit reload', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', request => requests.push(`${request.url()} ${request.postData() ?? ''}`));
  await page.getByLabel('내 판단과 근거', { exact: true }).fill('private-edited-judgment-not-for-server');
  await page.getByRole('button', { name: '이 브라우저에 저장', exact: true }).click();
  await expect(page.getByTestId('saved-review-comparison')).toContainText('검토함에서 처음 읽은 판단');
  await expect(page.getByTestId('saved-review-comparison')).not.toContainText('private-edited-judgment-not-for-server');
  await page.getByRole('button', { name: '선택한 저장 메모 다시 읽기', exact: true }).click();
  await expect(page.getByTestId('saved-review-comparison')).toContainText('private-edited-judgment-not-for-server');
  expect(requests.join('\n')).not.toContain('private-edited-judgment-not-for-server');
});
