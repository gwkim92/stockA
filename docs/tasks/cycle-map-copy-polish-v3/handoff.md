# cycle-map-copy-polish-v3 handoff

## Status

- current status: completed.
- completed: task contract created.
- completed: `/cycle-map` copy and labels now describe macro/domain/theme/instrument paths as user-facing flow stages.
- completed: EC2 deployment and route/content smoke passed.

## Changes

- changed `노드`-centric copy to `흐름 항목`, `흐름 단계`, and `흐름 관계`.
- changed `validator` wording to `검증`.
- changed `AI 근거 노드` wording to `AI 판단 흐름`.
- changed `전파 영향` wording to `연결 영향`.
- changed `충돌 플래그` wording to `충돌 표시`.
- changed `thesis` wording to `투자 논리`.
- kept existing links to intelligence, recommendations, theme details, and stock details.
- did not change ontology, propagation, cycle, recommendation, broker/order, API, or DB logic.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-map-copy-polish-v3`
- passed: `git diff --check`
- passed: EC2 deploy from `origin/codex/local-mvp-runtime-aws-bootstrap`, Next build, and `stockanalysis-web.service` restart.
- passed: `http://127.0.0.1:13000/cycle-map` returned 200 and contained `흐름 경로 판정판`, `AI 판단 흐름`, `흐름 항목`, `충돌 표시`, `상위 흐름 연결`, `흐름 단계` with no `validator`, `AI 근거 노드`, `흐름 노드`, `충돌 플래그`, `thesis`, `flag`, `artifact`, or `runner`.
- passed: Playwright snapshot smoke for `/cycle-map` found required Korean terms and no targeted jargon.

## Exact Next Step

- exact next step: continue page-by-page UX refactor with `/stocks` and `/stocks/[symbol]`, because stock pages need to connect direct news, upper-flow impacts, cycle state, professional analysis, and recommendation boundary more clearly.

## Notes

- frontend visibility only.
- ontology, propagation, cycle, recommendation, broker/order, API, and DB logic are not changed.
- commit: `a522e5fd`.
