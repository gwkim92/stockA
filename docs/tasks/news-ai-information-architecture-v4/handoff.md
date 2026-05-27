# news-ai-information-architecture-v4 Handoff

## Status

- completed: local implementation, EC2 deployment, and route smoke are complete.

## Completed

- completed: created task contract.
- completed: reduced `/intelligence` fetch/default display sizes in local code.
- completed: added full-list CTAs for source news, AI candidates, structured results, and blocked candidates.
- completed: added AI evidence detail source preview fallback to prefer translated cluster events.
- completed: deployed commits `385b9e6` and `61c397d` to EC2 and restarted `stockanalysis-web.service`.

## Verification

- `cd apps/web && npm run typecheck`: passed locally.
- `cd apps/web && npm run build`: passed locally.
- `git diff --check`: passed locally.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-information-architecture-v4`: passed locally.
- EC2 `cd apps/web && npm run typecheck`: passed.
- EC2 `cd apps/web && npm run build`: passed.
- EC2 `systemctl is-active stockanalysis-web.service`: `active`.
- EC2 and local tunnel route smoke:
  - `/intelligence`: `대표 흐름만 먼저 본다`, `AI 후보 전체 보기` rendered.
  - `/ai-evidence/ai-evidence-251`: `한국어 번역 확인` rendered and `한국어 번역 없음` absent.

## Next Step

- exact next step: start the next page-level UX slice, likely `data-health-decision-gate-redesign-v2`, to split operator run logs from user-facing status.

## Notes

- This task is frontend information architecture only.
- Recommendation weights and order boundaries remain unchanged.
