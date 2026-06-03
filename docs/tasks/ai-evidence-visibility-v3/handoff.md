# ai-evidence-visibility-v3 Handoff

## Status

- status: implemented_and_ec2_smoked
- started_at: 2026-05-27
- current status: implemented, committed, pushed, deployed to EC2, and smoke verified.
- completed: API visibility trace payload, frontend trace board, Korean labels, DTO typing, targeted backend test, typecheck, build.
- completed: EC2 deploy, API smoke, route smoke.
- reopened: 2026-06-04 clarity pass to make the detail-page top summary explicitly answer where the evidence can be used.

## Current Decision

- Keep the screen read-only.
- Show AI review results as evidence trace, not as a manual approval workflow.
- Do not add approval/rejection buttons until audit write API and RBAC write policy exist.
- The 2026-06-04 clarity pass does not change API, DB, scoring, scheduler, AI batch, or broker/order flow. It reuses existing `visibility_trace`, translation, and evidence neighborhood data.

## Next Step

- exact next step: continue `cycle-quality-audit-hardening-v1` so duplicate clusters, wrong theme attachment, unsupported ticker linkage, and macro-flow-vs-error classification are audited automatically and surfaced on `/data-health` and AI evidence screens.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- 2026-06-04 clarity pass: `cd apps/web && npm run typecheck` passed.
- 2026-06-04 clarity pass: `cd apps/web && npm run build` passed.
- 2026-06-04 clarity pass: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter` passed.
- 2026-06-04 clarity pass: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-visibility-v3` passed.
- 2026-06-04 clarity pass: `git diff --check` passed.
- 2026-06-04 clarity pass EC2: `npm run typecheck`, `npm run build`, `stockanalysis-web.service active`, deployed commit `c5859aa`.
- 2026-06-04 clarity pass EC2 route smoke: `/api/ai-evidence/ai-evidence-251` returned `visibility_trace.steps=[source, translation, ai_structure, validator, recommendation_linkage]`, validator `passed`; `/ai-evidence/ai-evidence-251` rendered `이 근거의 현재 사용처`, `원천 뉴스`, `한국어 번역`, `AI 구조화`, `자동 검증`, `추천·주문 경계`, `증권사 주문은`, `근거 사용 경로`.
- 2026-06-04 clarity pass user tunnel/browser smoke: `http://127.0.0.1:13000/ai-evidence/ai-evidence-251` rendered the same eight strings.

## EC2 Verification

- deployed commit: `17deba7`.
- `stockanalysis-frontend-api.service`: active.
- `stockanalysis-web.service`: active.
- EC2 targeted backend test passed for `test_live_ai_evidence_detail_response_exposes_news_event_candidate_artifact`.
- EC2 Next production build passed.
- `/api/ai-evidence/ai-evidence-251`: `visibility_trace.steps=[source, translation, ai_structure, validator, recommendation_linkage]`, `source.status=available`, `translation.status=available`, `validator.status=passed`, `target_symbol=SPY`, no vector storage URI or read-token env name in response.
- `/ai-evidence/ai-evidence-251`: HTTP 200 and rendered `한눈에 보는 근거 흐름`, `이 근거가 어디서 와서 어디에 쓰이는지 확인한다`, `검증 결과`, `실시간 AI 호출 없음`.

## Risks

- Recommendation linkage comes from the separately loaded evidence neighborhood. The API trace can state the candidate symbol, but the final linked recommendation count is filled on the frontend from neighborhood data.
