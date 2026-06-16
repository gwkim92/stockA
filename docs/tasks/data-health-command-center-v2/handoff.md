# data-health-command-center-v2 Handoff

## Status

- in progress.

## Current Status

- 상태: implementation started.
- 기준일: 2026-06-16
- 완료:
  - task contract created.
  - current `/data-health` render structure inspected.
- 막힌 점:
  - none.

## Intended Change

- Add a command-center section that groups data-health into immediate action, automation, data/AI quality, investment safety, and source limits.
- Remove or compress duplicate top priority cards so the first screen does not repeat the same judgment twice.
- Preserve detailed audit/log sections lower on the page.

## Verification

- Pending:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-command-center-v2`
  - EC2 route/browser smoke.

## Next Step

- exact next step: implement the command-center section and responsive CSS, then run local verification.
