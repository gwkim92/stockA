import { test, expect, type Page } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { draftKey, type Draft } from '../../src/lib/company-review-model';
const api = 'http://127.0.0.1:18770';
const route = '/stocks/AAPL/review';
const currentId = 'instrument-aapl';
const draft = (instrumentId = currentId, note = '선택한 저장 판단'): Draft => ({ version: 1, symbol: 'AAPL', instrumentId,
  snapshot: 'a'.repeat(64), asOf: '2026-09-01', savedAt: '2026-09-07T01:00:00Z', note,
  opposition: '저장된 반대 근거', nextAction: '이전 질문을 현재 자료와 대조', nextDate: '', checks: ['numbers'] });
async function seed(page: Page, notes: Draft[]) {
  await page.goto('/research-notes');
  await page.evaluate(entries => { for (const [key, value] of entries) localStorage.setItem(key, value); }, notes.map(value => [draftKey(value), JSON.stringify(value)]));
}
async function saveCurrent(page: Page) {
  await page.goto(route);
  await page.getByLabel('내 판단과 근거', { exact: true }).fill('실제 저장한 나의 판단');
  await page.getByLabel('반대 근거와 남은 의문', { exact: true }).fill('확인할 반대 가능성');
  await page.getByRole('button', { name: '이 브라우저에 저장', exact: true }).click();
  await expect(page.getByTestId('review-draft')).toContainText('이 브라우저에 저장했습니다');
}
const comparison = (page: Page) => page.getByTestId('saved-review-comparison');
test.beforeEach(async ({ request }) => { await request.post(`${api}/__scenario`, { data: { scenario: 'healthy' } }); });

test('actual inbox selection carries the exact saved identity and renders an accessible comparison', async ({ page }, info) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await saveCurrent(page);
  await page.getByRole('link', { name: '내 검토함 →', exact: true }).click();
  await page.getByRole('button', { name: 'AAPL 저장된 메모 열기', exact: true }).click();
  await expect(page.getByRole('link', { name: '현재 분석과 다시 검토 →', exact: true })).toHaveAttribute('href', `${route}?savedInstrument=${currentId}`);
  await page.getByRole('link', { name: '현재 분석과 다시 검토 →', exact: true }).click();
  await expect(comparison(page)).toContainText('저장 당시와 같은 분석 묶음');
  await expect(comparison(page)).toContainText('실제 저장한 나의 판단');
  await expect(comparison(page)).toContainText('합성 검증 자료');
  await expect(page.getByRole('button', { name: '이 브라우저에 저장', exact: true })).toBeEnabled();
  await comparison(page).scrollIntoViewIfNeeded();
  expect((await new AxeBuilder({ page }).include('[data-testid="saved-review-comparison"]').analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  expect(errors).toEqual([]);
  await page.screenshot({ path: info.outputPath(`continuity-${info.project.name}-comparison.png`), animations: 'disabled' });
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await page.screenshot({ path: info.outputPath(`continuity-${info.project.name}-full.png`), fullPage: true, animations: 'disabled' });
});

test('an old instrument note is not loaded into the current company editor', async ({ page }) => {
  const old = draft('instrument-old', '別の企業の過去メモ'), current = draft(currentId, '현재 기업 별도 메모');
  await seed(page, [old, current]);
  await page.getByRole('button', { name: '목록 새로고침', exact: true }).click();
  await page.getByRole('button', { name: 'AAPL · instrument-old 저장된 메모 열기', exact: true }).click();
  await page.getByRole('link', { name: '현재 분석과 다시 검토 →', exact: true }).click();
  await expect(comparison(page)).toContainText('기업 식별자가 다릅니다');
  await expect(comparison(page)).toContainText(old.note);
  await expect(page.getByTestId('review-draft')).toHaveCount(0);
  expect(await page.evaluate(key => localStorage.getItem(key), draftKey(old))).toBe(JSON.stringify(old));
  expect(await page.evaluate(key => localStorage.getItem(key), draftKey(current))).toBe(JSON.stringify(current));
  await page.getByRole('link', { name: '현재 기업의 별도 검토 열기 →', exact: true }).click();
  await expect(page.getByLabel('내 판단과 근거', { exact: true })).toHaveValue(current.note);
  await expect(comparison(page)).toHaveCount(0);
});

test('changed basis preserves old checks until existing explicit migration is chosen', async ({ page }) => {
  const old = draft(); await seed(page, [old]);
  await page.goto(`${route}?savedInstrument=${currentId}`);
  await expect(comparison(page)).toContainText('저장 당시와 다른 분석 묶음');
  await expect(page.getByRole('button', { name: '이 브라우저에 저장', exact: true })).toBeDisabled();
  expect(await page.evaluate(key => localStorage.getItem(key), draftKey(old))).toBe(JSON.stringify(old));
  await page.getByRole('button', { name: '메모만 가져와 새 기준으로 검토', exact: true }).click();
  await expect(page.getByLabel('숫자·통화·기간을 원천과 대조했다', { exact: true })).not.toBeChecked();
  await expect(page.getByLabel('내 판단과 근거', { exact: true })).toHaveValue(old.note);
});

for (const kind of ['missing', 'corrupt', 'denied'] as const) {
  test(`${kind} selected note is not substituted and does not expose an unrelated editor`, async ({ page }) => {
    await seed(page, [draft()]);
    if (kind === 'corrupt') await page.evaluate(key => localStorage.setItem(key, 'broken-original'), draftKey(draft('instrument-old')));
    if (kind === 'denied') await page.addInitScript(() => { Object.defineProperty(window, 'localStorage', { get() { throw new DOMException('denied', 'SecurityError'); } }); });
    await page.goto(`${route}?savedInstrument=instrument-old`);
    const message = { missing: '선택한 메모가 이 브라우저에 없습니다', corrupt: '형식이나 기업 식별 정보를 확인할 수 없습니다', denied: '브라우저 저장소를 읽을 수 없습니다' }[kind];
    await expect(comparison(page)).toContainText(message);
    await expect(page.getByTestId('review-draft')).toHaveCount(0);
    if (kind !== 'denied') expect(await page.evaluate(key => localStorage.getItem(key), draftKey(draft()))).toBe(JSON.stringify(draft()));
  });
}

for (const query of ['savedInstrument=..%2Fprivate', 'savedInstrument=', 'savedInstrument=instrument-aapl&savedInstrument=instrument-old']) {
  test(`invalid or duplicate reference ${query} performs no review storage reads`, async ({ page }) => {
    await page.addInitScript(() => {
      const original = Storage.prototype.getItem;
      (window as unknown as { reviewReads: string[] }).reviewReads = [];
      Storage.prototype.getItem = function(key: string) {
        if (key.startsWith('stocka:company-review:')) (window as unknown as { reviewReads: string[] }).reviewReads.push(key);
        return original.call(this, key);
      };
    });
    await page.goto(`${route}?${query}`);
    await expect(comparison(page)).toContainText('메모 식별자가 올바르지 않습니다');
    await expect(page.getByTestId('review-draft')).toHaveCount(0);
    expect(await page.evaluate(() => (window as unknown as { reviewReads: string[] }).reviewReads)).toEqual([]);
  });
}

test('source switching preserves saved identity, selected comparison and unsaved editor text', async ({ page }) => {
  await saveCurrent(page); await page.goto(`${route}?savedInstrument=${currentId}`);
  await expect(comparison(page)).toContainText('실제 저장한 나의 판단');
  await page.getByLabel('내 판단과 근거', { exact: true }).fill('아직 저장하지 않은 추가 검토');
  await page.getByRole('radio', { name: /규제 비용과 반대 가능성/ }).check();
  await expect(page.getByTestId('review-source-content')).toContainText('regulatory costs');
  expect(new URL(page.url()).searchParams.get('savedInstrument')).toBe(currentId);
  await expect(page.getByLabel('내 판단과 근거', { exact: true })).toHaveValue('아직 저장하지 않은 추가 검토');
  await expect(comparison(page)).toContainText('실제 저장한 나의 판단');
  await expect(comparison(page)).not.toContainText('아직 저장하지 않은 추가 검토');
});

test('external updates mark the comparison stale without silently replacing its saved baseline', async ({ page, context }) => {
  await saveCurrent(page); await page.goto(`${route}?savedInstrument=${currentId}`);
  await expect(comparison(page)).toContainText('실제 저장한 나의 판단');
  const other = await context.newPage(); await other.goto('/research-notes');
  await other.evaluate(key => { const value = JSON.parse(localStorage.getItem(key)!); value.note = '다른 탭의 수정'; localStorage.setItem(key, JSON.stringify(value)); }, draftKey(draft()));
  await expect(comparison(page)).toContainText('다른 탭에서 선택한 메모가 변경됐습니다');
  await expect(comparison(page)).not.toContainText('다른 탭의 수정');
  await page.getByRole('button', { name: '선택한 저장 메모 다시 읽기', exact: true }).click();
  await expect(comparison(page)).toContainText('다른 탭의 수정'); await other.close();
});

test('a filtered-out selected note cannot remain as the apparent current comparison target', async ({ page }) => {
  await seed(page, [draft()]); await page.getByRole('button', { name: '목록 새로고침', exact: true }).click();
  await page.getByRole('button', { name: 'AAPL 저장된 메모 열기', exact: true }).click();
  await page.getByLabel('종목·메모에서 찾기', { exact: true }).fill('no matching note');
  await expect(page.getByTestId('saved-review-reader')).toContainText('현재 검색·날짜 필터에 포함되지 않습니다');
  await expect(page.getByRole('link', { name: '현재 분석과 다시 검토 →', exact: true })).toHaveCount(0);
  await page.getByLabel('종목·메모에서 찾기', { exact: true }).fill('');
  await expect(page.getByTestId('saved-review-reader')).toContainText('선택한 저장 판단');
});
