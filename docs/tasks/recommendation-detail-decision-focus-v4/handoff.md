# recommendation-detail-decision-focus-v4 Handoff

## Status

- completed and deployed to EC2.

## Current Status

- 상태: local verification, EC2 deploy, route smoke, and in-app browser smoke passed.
- 기준일: 2026-06-16
- 완료:
  - task contract created.
  - current `/recommendations/[recommendationId]` structure inspected.
  - added a `추천서 읽는 순서` focus panel above the existing professional waterfall.
  - prioritized first action across source blocker, blocked step, paper validation block, outcome wait, and review path.
  - added focus cards for evidence path, financial/valuation checks, and market correlation.
  - changed the recommendation waterfall from a fixed seven-column grid to a responsive grid.
  - deployed commit `0794c7a1` to EC2 `develop`.
- 막힌 점:
  - none.

## Intended Change

- Add a focused “추천서 읽는 순서” panel above the existing professional waterfall.
- Show the first action: source blocker, blocked professional step, paper validation block, outcome wait, or evidence review.
- Keep the existing waterfall and detail sections as drill-down, but make the first scan path explicit.

## Verification

- Passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-decision-focus-v4`
  - EC2 deploy: `git pull --ff-only origin develop`, `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`; service state `active`; commit `0794c7a1`.
  - EC2 route smoke:
    - `/recommendations`: server error absent.
    - `/recommendations/recommendation-346`: `추천서 읽는 순서`, `근거 경로 보기`, `시장 동조성 보기`, `현재 결론`, `거시`, `테마`, `기업`, `재무`, `밸류에이션`, `리스크`; server error absent.
  - in-app browser smoke through `http://127.0.0.1:13000/recommendations/recommendation-346`:
    - focus panel card count `4`.
    - first card: `성과 측정 대기 상태 확인`.
    - evidence card: `AI 2개 · 흐름 0개`.
    - financial card: `재무 12개 · 재무항목 5개`.
    - market card: `비교 8개`.
    - waterfall grid: `repeat(auto-fit, minmax(210px, 1fr))`.
    - server error absent.

## Next Step

- exact next step: continue the global UX refactor with `/data-health` grouping so monitoring separates open gates, managed waits, source limits, scheduler status, and alert/auth readiness in user-readable Korean.

## Risks

- This task is visibility-only. It does not prove recommendation quality, valuation accuracy, or future return.
- Recommendation weights, benchmark definitions, portfolio positions, schema, paper execution logic, broker submit, and live trading behavior were not changed.
