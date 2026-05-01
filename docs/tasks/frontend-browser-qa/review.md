# Review Notes

## Scope Review

- 작업 범위는 browser smoke QA와 그 과정에서 확인된 static icon/layout 결함 수정으로 제한했다.
- scoring, thesis policy, portfolio recommendation logic, live data adapter는 변경하지 않았다.

## Verification Evidence

- Playwright home route:
  - URL: `http://127.0.0.1:3000/`
  - title: `Stockanalysis Cockpit`
  - console: errors 0, warnings 0
  - screenshot: `output/playwright/home-after-fix.png`
- Playwright recommendation detail:
  - URL: `http://127.0.0.1:3000/recommendations/AAPL-2024-11-01`
  - title: `Recommendation Detail | Stockanalysis Cockpit`
  - console: errors 0, warnings 0
  - screenshot: `output/playwright/recommendation-detail.png`
- Playwright thesis detail:
  - URL: `http://127.0.0.1:3000/theses/AAPL-bootstrap-v1`
  - title: `Thesis Detail | Stockanalysis Cockpit`
  - console: errors 0, warnings 0
  - screenshot: `output/playwright/thesis-detail.png`
- Playwright portfolio coverage:
  - URL: `http://127.0.0.1:3000/portfolio/coverage`
  - title: `Portfolio Coverage | Stockanalysis Cockpit`
  - console: errors 0, warnings 0
  - screenshot: `output/playwright/portfolio-coverage.png`
- Playwright mobile smoke:
  - viewport: `390x844`
  - screenshot: `output/playwright/home-mobile.png`
- Static asset request:
  - `/icon.svg`: 200 OK
- Script verification:
  - `bash scripts/verify_frontend_detail_routes.sh`: 통과
  - includes `npm run typecheck`, `next build`, route smoke, fixture server regression
- Harness verification:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-qa`: 통과
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Residual Risks

- screenshots are local ignored artifacts, not repository evidence.
- production visual QA is not captured; production route/build smoke is covered by `scripts/verify_frontend_detail_routes.sh`.
