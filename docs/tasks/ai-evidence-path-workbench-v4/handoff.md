# ai-evidence-path-workbench-v4 Handoff

## Status

- implemented locally; pending commit, EC2 deploy, and route smoke.

## Current Status

- 상태: local verification passed.
- 기준일: 2026-06-14
- 완료:
  - task contract created.
  - added reusable `EvidencePathWorkbench` for the fixed source -> translation -> AI structure -> validator -> recommendation/order path.
  - applied the workbench to `/ai-evidence/[evidenceId]`.
  - applied the workbench to `/ai-evidence/results`.
  - applied the workbench to `/ai-evidence/blocked`.
  - added mini evidence paths to news cluster cards in `/ai-evidence/results`.
  - added responsive CSS for the shared workbench and mini paths.
- 막힌 점:
  - none.

## Verification

- Passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-path-workbench-v4`

## Exact Next Step

- exact next step: commit/push to `develop`, pull on EC2, rebuild/restart Next service, then smoke `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, and one `/ai-evidence/[id]`.

## Notes

- This is visibility-only. Do not change recommendation weights, benchmark definitions, portfolio positions, schema, or broker/order boundaries.
