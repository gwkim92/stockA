# Session Handoff

## Active Task

- 이름: frontend-browser-qa
- 담당: Codex
- 날짜: 2026-05-01

## Current Status

- 완료:
  - 홈, recommendation detail, thesis detail, portfolio coverage 경로를 Playwright로 열었다.
  - `icon.svg`와 `metadata.icons`를 추가해 favicon/static icon 404를 제거했다.
  - review queue action row를 2줄 grid layout으로 변경해 텍스트 겹침을 줄였다.
  - `output/`과 `.playwright-cli/`를 ignore 대상으로 추가했다.
  - 정식 verification script와 AWH 검증을 최신 변경 기준으로 통과시켰다.
- 막힌 점:
  - 현재 없음.

## Files Touched

- 생성:
  - `apps/web/src/app/icon.svg`
  - `docs/tasks/frontend-browser-qa/contract.md`
  - `docs/tasks/frontend-browser-qa/plan.md`
  - `docs/tasks/frontend-browser-qa/handoff.md`
  - `docs/tasks/frontend-browser-qa/review.md`
- 수정:
  - `.gitignore`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/frontend-detail-routes/handoff.md`
  - `docs/tasks/frontend-detail-routes/review.md`

## Decisions

- screenshots and Playwright session logs are local artifacts and must not be committed.
- static icon is repo-owned because the public Next app should not emit missing asset requests.
- browser QA does not change DTOs, fixture payloads, score logic, or recommendation policy.

## Verification Already Run

- Playwright `open http://127.0.0.1:3000`: page title `Stockanalysis Cockpit`, console errors 0, warnings 0.
- Playwright `/recommendations/AAPL-2024-11-01`: page title `Recommendation Detail | Stockanalysis Cockpit`, console errors 0, warnings 0.
- Playwright `/theses/AAPL-bootstrap-v1`: page title `Thesis Detail | Stockanalysis Cockpit`, console errors 0, warnings 0.
- Playwright `/portfolio/coverage`: page title `Portfolio Coverage | Stockanalysis Cockpit`, console errors 0, warnings 0.
- Playwright requests with static assets: `/icon.svg` returned 200 OK.
- Screenshots captured under ignored `output/playwright/`.
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-qa`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- production browser visual QA. 현재 production build route smoke는 script에서 수행했고, visual QA는 Next dev server 기준으로 수행했다.

## Exact Next Step

- 다음 세션은 이것부터 시작: AI evidence/source document route 확장 여부를 결정하거나, `feature/frontend-detail-routes`를 `develop`으로 PR/merge한다.

## Risks

- Mobile screenshot includes the Next dev indicator overlay. This is a development-server artifact, not part of production UI.
- Live data freshness remains outside this task.
