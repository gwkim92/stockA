# decision-cockpit-recommendation-boundary-summary-v1 Contract

## Task Request

- request: 홈과 추천 목록에서도 추천 상세의 판단 경계를 요약해 "오늘 뭘 봐야 하는지"를 더 직접적으로 보여준다.
- context: 추천 상세와 종목 상세에는 전문 판단/페이퍼/주문 경계가 보이기 시작했다. 목록과 첫 화면에도 같은 경계가 있어야 사용자가 어디부터 볼지 알 수 있다.

## Goal

- goal: `/api/recommendations`, `/recommendations`, `/`가 추천 후보의 검토 가능 여부, 페이퍼 검증 대기, evidence 차단, 주문 차단을 명확히 보여준다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/decision-cockpit-recommendation-boundary-summary-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change schema, benchmark, portfolio positions, broker/order flow, or live trading behavior.
- Do not synthesize financials for source-blocked symbols.
- Do not introduce paid external services.

## Scope

- Add read-only `decision_boundary` metadata to recommendation list rows.
- Add boundary counts to recommendation list summary.
- Render those counts on the home page and recommendation list.
- Keep order boundary as `read_only_no_order`.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task decision-cockpit-recommendation-boundary-summary-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Recommendation list API exposes decision boundary status and counts.
- [x] `/recommendations` shows judgment boundary per candidate.
- [x] `/` shows recommendation boundary counts in today's decision area.
- [x] Local verification passes.
- [ ] EC2 route smoke confirms live rendering.
