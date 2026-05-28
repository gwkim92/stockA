# stocks-list-decision-ux-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot passed.

## Current Decision

- This is a frontend visibility slice only.
- The stock list API does not expose professional source blocker counts. The list should not invent those counts; it should route users to stock detail for professional/source evidence.
- No scoring, broker, paper validation, portfolio, benchmark, or order state is mutated.

## Next Step

- exact next step: continue the UX/UI refactor with `/portfolio/coverage`, because it still mixes risk-budget operations, review status, and investment-facing guidance.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-list-decision-ux-v2`
- passed: `git diff --check`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service` returned `active`.
- passed on EC2: `http://127.0.0.1:3000/stocks` rendered `종목 판정판`, `추천 연결`, `보유 연결`, `관찰 종목`, `데이터 점검`, and `종목별 상세와 추천 근거로 바로 이동한다`.
- passed through local tunnel: `http://127.0.0.1:13000/stocks` rendered the same strings.
- passed via Playwright snapshot: `http://127.0.0.1:13000/stocks` exposed the command panel and four core cards.

## Risks

- This task improves comprehension only. It does not add professional source blocker data to the stock list API.
- If users need source-blocked counts directly on `/stocks`, that should be a separate backend/API visibility task.
