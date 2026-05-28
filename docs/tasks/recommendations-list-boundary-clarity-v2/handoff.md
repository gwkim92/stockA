# recommendations-list-boundary-clarity-v2 Handoff

## Status

- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright snapshot passed.

## Current Decision

- This is a frontend visibility slice only.
- The page should start with a decision panel, not an operator-style log or repeated explanation.
- Recommendation rows remain read-only links to detail pages. No scoring, broker, paper validation, portfolio, benchmark, or order state is mutated.

## Next Step

- exact next step: continue the UX/UI refactor with the next high-traffic page that still mixes operator wording and investor wording, likely `/stocks` or `/portfolio/coverage`.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendations-list-boundary-clarity-v2`
- passed: `git diff --check`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service` returned `active`.
- passed on EC2: `http://127.0.0.1:3000/recommendations` rendered `추천 신호 판정판`, `추천 신호`, `페이퍼 대기`, `주문 차단`, `전문 분석 근거`, and `최신 추천 후보를 근거별로 연다`.
- passed through local tunnel: `http://127.0.0.1:13000/recommendations` rendered the same strings.
- passed via Playwright snapshot: `http://127.0.0.1:13000/recommendations` exposed the command panel and four core cards.

## Risks

- This task improves comprehension only. It does not improve recommendation quality or outcome maturity.
- If upstream API fields are missing in older deployments, the page still depends on the existing recommendation list contract.
