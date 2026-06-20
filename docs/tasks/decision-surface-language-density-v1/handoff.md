# decision-surface-language-density-v1 Handoff

## Current Status

- status: implemented_and_ec2_smoked
- completed: local implementation, Next typecheck, Next production build, `git diff --check`, AWH verify, GitHub push, EC2 pull/build/restart, EC2 route smoke, and local tunnel smoke passed.
- branch: `develop`

## What Changed

- `/cycles` now leads with the cycle to inspect first and shorter risk-oriented copy.
- `/paper-trading` separates actual submitted orders, virtual validation, and blocked execution without explaining internal screen mechanics.
- `/portfolio/coverage` leads with portfolio risk gaps and outcome maturity boundary.
- `/performance` states that current outcome samples are not yet enough to change recommendation formulas.
- Recommendation detail copy now uses investor-facing evidence language instead of internal AI/process labels.
- Global navigation and recommendation list copy now use `뉴스 근거` / `뉴스·투자 근거` instead of `뉴스·AI` / `뉴스·AI 해석`.

## Boundaries Preserved

- API contracts unchanged.
- Database schema unchanged.
- Scheduler cadence unchanged.
- Recommendation scoring weights unchanged.
- Benchmark definitions, portfolio positions, paper records, broker/order boundary, and live trading unchanged.
- Read-only/no-order boundary remains visible.

## Verification To Run

- exact next step: continue with a deeper layout/information-architecture pass for pages not covered by this copy-density task, starting with `/source-documents/[documentId]`, `/ai-evidence/[evidenceId]`, and `/stocks/[symbol]`.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-surface-language-density-v1`
- `git diff --check`

## Verification Evidence

- local passed: `cd apps/web && npm run typecheck`
- local passed: `cd apps/web && npm run build`
- local passed: `git diff --check`
- local passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-surface-language-density-v1`
- pushed commits: `2293caa6`, `60b6a74a`
- EC2 deployed commit: `60b6a74a`
- EC2 active services: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`
- EC2 route smoke passed: `/cycles`, `/paper-trading`, `/performance`, `/portfolio/coverage`, `/recommendations`, `/recommendations/recommendation-67`
- local tunnel `http://127.0.0.1:13000` route smoke passed: `/`, `/recommendations`, `/recommendations/recommendation-67`, `/cycles`, `/paper-trading`
- forbidden user-facing terms absent on smoke routes: `뉴스·AI`, `AI 해석`, `추천서 읽는 순서`, `판단 순서`, `처리 순서`, `주문 버튼`, `추천 weight`

## EC2 Smoke Targets

- `/cycles`
- `/paper-trading`
- `/performance`
- `/portfolio/coverage`
- `/recommendations/<active recommendation id>`

## Remaining Risk

- This task improves copy density and decision hierarchy only. It does not redesign global navigation, chart composition, or information architecture beyond the touched pages.
