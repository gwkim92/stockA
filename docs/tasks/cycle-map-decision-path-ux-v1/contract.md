# cycle-map-decision-path-ux-v1 Contract

## Task Request

- request: Continue the frontend UX refactor by making `/cycle-map` easier to understand as an investment decision flow.
- context: The cycle map already shows nodes, lanes, and relationships, but the page still feels like a technical graph/status dump. The user needs to understand which cycle matters today, why it matters, which symbols are exposed, and where to verify recommendations.

## Goal

- goal: `/cycle-map` should read as `상위 흐름 -> 사이클 상태 -> 노출 종목 -> 추천/검증 화면` instead of a repeated graph card list.

## Scope

- Include:
  - clarify the top decision summary.
  - add a compact decision path strip for the top cycle flows.
  - replace the repeated detailed card block with a traceable flow table.
  - improve Korean wording and remove operator/debug phrasing.
  - update CSS for readability and responsive layout.
  - local and EC2 route smoke.
- Exclude:
  - backend schema changes.
  - cycle scoring changes.
  - recommendation score/weight changes.
  - portfolio position changes.
  - broker/order flow.
  - external RAG/vector/graph services.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/cycle-map-decision-path-ux-v1/*`

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-map-decision-path-ux-v1`
- verification command: route smoke for `/cycle-map`

## Acceptance Criteria

- The page answers: `오늘 무엇을 먼저 봐야 하나`, `왜 이 흐름인가`, `어떤 종목이 노출됐나`, `어디서 추천/근거를 확인하나`.
- The page explicitly states cycle data is context, not an automatic buy/sell signal.
- Top cycle flows expose parent flow, node, child/target symbols, evidence counts, and next action.
- No recommendation scoring, order boundary, benchmark, or portfolio position mutation is introduced.
