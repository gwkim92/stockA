# visual-quality-hard-gate-v1 Contract

## Task Request

- 실제 브라우저 QA와 자동 검사를 강화한다.
- request: UX 정상화 작업 후 실제 브라우저에서 투자자 화면과 운영 콘솔 화면을 검증하고, raw 내부 용어와 모바일 overflow가 다시 노출되지 않도록 자동 hard gate를 강화한다.

## Goal

- goal: `/portfolio/coverage`, `/paper-trading`, `/stocks/AAPL`, live recommendation detail, 운영 콘솔 route가 375px, 768px, 1280px에서 읽히고 내부 실행 용어 없이 표시되는지 증거를 남긴다.
- goal: 브라우저 스크린샷과 Playwright e2e를 통해 회사 주식/추천/포트폴리오/가상 매매 화면의 문구, 줄바꿈, horizontal overflow, raw status code 노출을 검증한다.

## Scope

- Extend Playwright checks for 375px, 768px, and 1280px.
- Check primary investor routes, detail routes, portfolio, paper, and operations.
- Capture screenshot evidence under `output/playwright/visual-quality-hard-gate-v1/`.
- Confirm React dev tooling gate: `react-grab`, `react-scan`, and `react-doctor`.

## Invariants

- Do not weaken tests to pass.
- Do not hide content to pass audits.

## Mutable Surface

- mutable surface:
  - `apps/web/tests/e2e/investment-workspace.spec.ts`
  - `apps/web/src/lib/presentation/**`
  - `apps/web/src/app/**/_components/**`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/components/candlestick-chart.tsx`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`
  - `docs/tasks/visual-quality-hard-gate-v1/**`

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter tests.test_frontend_fixture_server -v`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task visual-quality-hard-gate-v1`
- browser screenshots exist for target routes.
- forbidden investor copy scan passes.
- production build route smoke passes.
