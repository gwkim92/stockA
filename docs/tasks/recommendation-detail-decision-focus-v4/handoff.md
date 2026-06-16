# recommendation-detail-decision-focus-v4 Handoff

## Status

- in progress.

## Current Status

- 상태: implementation started.
- 기준일: 2026-06-16
- 완료:
  - task contract created.
  - current `/recommendations/[recommendationId]` structure inspected.
- 막힌 점:
  - none.

## Intended Change

- Add a focused “추천서 읽는 순서” panel above the existing professional waterfall.
- Show the first action: source blocker, blocked professional step, paper validation block, outcome wait, or evidence review.
- Keep the existing waterfall and detail sections as drill-down, but make the first scan path explicit.

## Verification

- Pending:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-decision-focus-v4`
  - EC2 route/browser smoke.

## Next Step

- exact next step: implement the recommendation focus panel and responsive CSS, then run local verification.
