# recommendation-professional-decision-clarity-v1 Contract

## Task Request

- request: 추천 상세와 종목 상세에서 "왜 이 종목인가"를 전문 분석 순서로 더 명확하게 보여준다.
- context: `professional-analysis-depth-v2`로 data-health의 분석 깊이 가시성은 확보했다. 다음 병목은 사용자가 추천/종목 상세에서 판단 흐름과 차단 경계를 바로 이해하는 것이다.

## Goal

- goal: `/recommendations/[id]`와 `/stocks/[symbol]`이 거시/뉴스/사업/재무/밸류에이션/thesis/포지션/페이퍼 검증 순서를 더 선명하게 보여주고, 원천 차단과 주문 차단을 투자자 언어로 표시한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/components/professional-research-flow.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `docs/tasks/recommendation-professional-decision-clarity-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not change backend SQL, schema, benchmark, portfolio position, or broker/order flow.
- Do not synthesize financials for source-blocked symbols.
- Do not introduce paid external data/RAG/vector/graph tooling.
- Do not trigger live LLM calls from a page request.

## Scope

- Add a compact professional flow summary to the shared research-flow component.
- Add a recommendation decision boundary rail that explains paper validation, score policy, source-blocked steps, and order boundary.
- Add a stock detail professional guardrail panel that explains whether professional decision and paper validation inputs are allowed.
- Fix obvious duplicate stock detail wording while touching the page.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-professional-decision-clarity-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Recommendation detail shows the professional decision boundary clearly.
- [x] Stock detail shows source guardrail and paper/order boundary clearly.
- [x] Shared research flow gives ready/watch/blocked counts.
- [x] Local verification passes.
- [ ] EC2 route smoke confirms live rendering.
