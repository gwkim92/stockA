# ai-evidence-visibility-v3 Contract

## Task Request

- request: AI 근거 상세 화면에서 원천 뉴스, 한국어 번역, AI 구조화 결과, validator 통과/차단 이유, 추천 연결을 한 화면에서 추적 가능하게 정리한다.
- context: 사용자가 `/ai-evidence/{id}` 화면에서 무엇을 검토해야 하는지, 왜 뉴스가 묶였는지, 어떤 종목/추천과 연결되는지 이해하기 어렵다고 지적했다.

## Goal

- goal: `/api/ai-evidence/{id}`와 `/ai-evidence/{id}`가 “원천 → 번역 → AI 구조화 → validator → 추천/종목 연결” 5단계를 명확히 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/ai-evidence-visibility-v3/*`

## Invariants

- Do not enable human approval write API in this task.
- Do not call LLM from FastAPI or Next request path.
- Do not change recommendation scoring weights, portfolio positions, benchmark, outcome calibration, or broker/order flow.
- Do not expose DB URL, bearer token, webhook URL, vector storage URI, raw secret env, or hidden provider credentials.

## Scope

- Add a stable `visibility_trace` payload to AI evidence detail DTO.
- Render a user-facing Korean trace board that shows exactly what is known, what passed/failed, what is connected, and what the next screen is.
- Make validator pass/blocked status explicit.
- Make recommendation/thesis/stock connection explicit without implying this is an order or final recommendation.
- Keep detailed raw-ish model metadata behind existing details/metadata sections.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-visibility-v3`
- verification command: `git diff --check`

## Done Criteria

- [ ] API includes source/translation/AI/validator/recommendation visibility trace.
- [ ] AI evidence page renders the trace in Korean user-facing wording.
- [ ] Validator pass/blocked decision is visible without requiring developer terms.
- [ ] Recommendation and stock links are visible where available.
- [ ] Targeted verification and EC2 route smoke pass.
