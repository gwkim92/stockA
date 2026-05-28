# cycles-decision-ux-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot verification passed.

## Current Decision

- This is a frontend visibility slice only.
- `/cycles` should read as the theme-level cycle status board.
- `/cycle-map` should remain the graph/path view for macro-to-theme-to-instrument propagation.
- No scoring, API, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: continue the broader UX/page split sweep with `/cycle-map`, focusing on making macro-to-theme-to-instrument paths understandable without repeating `/cycles` status-board language.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycles-decision-ux-v2`
- passed: `git diff --check`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed: EC2 `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed: EC2 `sudo systemctl restart stockanalysis-web.service`
- passed: EC2 internal route smoke for `http://127.0.0.1:3000/cycles`
- passed: tunnel route smoke for `http://127.0.0.1:13000/cycles`
- passed: Playwright snapshot found `사이클 판정판`, `테마 상태를 보고, 원인 경로는 따로 확인한다`, `상태표`, `변화`, `근거 축`, and `상위 흐름 지도`

## Risks

- This task improves comprehension only. It does not improve cycle calculation accuracy.
- Detailed event-to-cycle causality remains on `/cycle-map`, theme detail, and evidence pages.
