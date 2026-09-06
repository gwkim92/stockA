// Temporary read-only layout diagnostic. No UI mutation or relaxed assertion.
import { test } from '@playwright/test';
test('capture shell and shadow layout metrics', async ({ page }, info) => {
  await page.goto('/stocks/AAPL/review');
  await page.getByTestId('review-source-content').waitFor();
  const geometry = await page.evaluate(() => {
    const elements: Element[] = [];
    const visit = (root: Document | ShadowRoot) => {
      for (const el of root.querySelectorAll('*')) {
        elements.push(el);
        if (el.shadowRoot) visit(el.shadowRoot);
      }
    };
    visit(document);
    const measure = (el: Element) => {
      const rect = el.getBoundingClientRect(), css = getComputedStyle(el);
      return { tag: el.tagName, id: el.id, cls: typeof el.className === 'string' ? el.className : 'svg',
        right: rect.right, left: rect.left, width: rect.width, scroll: el.scrollWidth, client: el.clientWidth,
        display: css.display, position: css.position, overflowX: css.overflowX, minWidth: css.minWidth,
        text: el.children.length === 0 ? (el.textContent ?? '').slice(0, 90) : '' };
    };
    return { width: document.documentElement.scrollWidth, viewport: innerWidth,
      roots: [document.documentElement, document.body, ...document.body.children].map(measure),
      overflow: elements.map(measure).filter(e => e.display !== 'none' &&
        (e.right > innerWidth + 1 || e.left < -1 || e.scroll > e.client + 1)).slice(0, 80) };
  });
  await info.attach('full-shell-geometry', { body: JSON.stringify(geometry), contentType: 'application/json' });
});
