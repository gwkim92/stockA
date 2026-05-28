# events-ledger-decision-ux-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot passed.

## Current Decision

- This is a frontend visibility slice only.
- The raw event ledger should explain the processing path before showing the long list.
- No AI extraction, validator, propagation, recommendation, broker, paper validation, order, or portfolio state is mutated.

## Next Step

- exact next step: continue the UX/UI refactor with `/events/classification` or `/cycles`, because both still need clearer user-facing decision hierarchy.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-ledger-decision-ux-v2`
- passed: `git diff --check`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service` returned `active`.
- passed on EC2: `http://127.0.0.1:3000/events` rendered `뉴스 이벤트 판정판`, `수집 원장`, `1차 분류`, `AI 연결`, `차단·보류`, and `원문이 들어왔는지보다, 판단 입력으로 쓸 수 있는지 본다`.
- passed through local tunnel: `http://127.0.0.1:13000/events` rendered the same strings.
- passed via Playwright snapshot: `http://127.0.0.1:13000/events` exposed the command panel and four core cards.

## Risks

- This task improves comprehension only. It does not improve event classification or AI extraction quality.
- The event list shows current API fields only; richer per-event validator detail remains on AI evidence pages.
