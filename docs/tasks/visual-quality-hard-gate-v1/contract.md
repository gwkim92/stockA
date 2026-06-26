# visual-quality-hard-gate-v1 Contract

## Request

- 실제 브라우저 QA와 자동 검사를 강화한다.

## Scope

- Extend Playwright checks for 375px, 768px, and 1280px.
- Check primary investor routes, detail routes, portfolio, paper, and operations.
- Capture screenshot evidence under `output/playwright/visual-quality-hard-gate-v1/`.
- Confirm React dev tooling gate: `react-grab`, `react-scan`, and `react-doctor`.

## Invariants

- Do not weaken tests to pass.
- Do not hide content to pass audits.

## Verification

- `cd apps/web && npm run test:e2e`
- browser screenshots exist for target routes.
- forbidden investor copy scan passes.
- production build route smoke passes.
