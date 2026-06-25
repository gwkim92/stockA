# recommendation-detail-professional-audit-disclosure-v1 Contract

## Task Request

- request: Continue recommendation detail UX/UI renewal after `recommendation-detail-score-audit-disclosure-v1`.
- request: Reduce the remaining lower professional audit area on `/recommendations/recommendation-471`.
- request: Keep expert evidence and guardrail details available, but move layer-by-layer audit details behind progressive disclosure.

## Goal

- goal: 추천 상세 하단의 `추천 전문 분석 감사` 영역을 투자자용 요약 우선 구조로 바꾼다.
- goal: 전문 분석 레이어 상세, 누락 레이어, 원천 차단 사유는 사라지지 않게 보존하되 기본 화면에서는 판단 요약과 차단 여부를 먼저 보여준다.
- goal: oversized recommendation detail page에서 전문 감사 렌더링과 라벨 변환 로직을 독립 컴포넌트로 분리한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- mutable surface: `apps/web/src/components/recommendation-professional-audit-model.ts`
- mutable surface: `apps/web/src/components/recommendation-professional-audit-panel.tsx`
- mutable surface: `apps/web/src/components/recommendation-professional-audit-panel.module.css`
- mutable surface: `apps/web/src/components/recommendation-professional-audit-panel.test.tsx`
- mutable surface: `docs/tasks/recommendation-detail-professional-audit-disclosure-v1/`

## Invariants

- No recommendation score weight changes.
- No benchmark, portfolio position, outcome, paper validation, broker submit, or order boundary mutation.
- Keep existing recommendation API shape and route URL.
- Preserve professional audit detail: source blocker, coverage, missing layers, layer checks, score policy, and order boundary must remain visible somewhere.
- Investor-facing summary must avoid `pipeline`, `runner`, `artifact`, raw DB field names, and English-only internal status codes.

## Verification

- verification command: `cd apps/web && npm test -- --run src/components/recommendation-professional-audit-panel.test.tsx`
- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-professional-audit-disclosure-v1`
- verification command: Browser QA on local latest production build with EC2 FastAPI tunnel at 375px, 768px, and 1280px.
- verification command: EC2 route smoke on `http://127.0.0.1:13000/recommendations/recommendation-471` after deployment.

## Acceptance Criteria

- The professional audit area starts with product type, coverage, blocked/waiting count, and order boundary.
- Layer-by-layer professional audit checks are hidden behind a disclosure control by default.
- Source blocker and missing layer labels remain accessible and understandable in Korean.
- The route keeps real order submission blocked and does not mutate recommendation results.
