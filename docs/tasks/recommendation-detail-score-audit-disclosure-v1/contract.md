# recommendation-detail-score-audit-disclosure-v1 Contract

## Task Request

- request: Continue recommendation detail UX/UI renewal after `recommendation-detail-executive-brief-v2`.
- request: Reduce the long lower score/evidence/audit area on `/recommendations/recommendation-471`.
- request: Show score and outcome summary first, and hide detailed calculation inputs behind progressive disclosure.

## Goal

- goal: 추천 상세 하단의 점수 근거와 성과 측정 영역을 투자자용 요약 우선 구조로 바꾼다.
- goal: 계산 입력과 출처 메타데이터는 필요할 때만 펼치도록 하여 `/recommendations/recommendation-471`에서 판단 흐름을 방해하지 않게 한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- mutable surface: `apps/web/src/app/globals.css`
- mutable surface: `apps/web/src/components/recommendation-score-audit-panel.tsx`
- mutable surface: `apps/web/src/components/recommendation-score-audit-panel.module.css`
- mutable surface: `apps/web/src/components/recommendation-score-audit-model.ts`
- mutable surface: `apps/web/src/components/recommendation-score-audit-panel.test.tsx`
- mutable surface: `apps/web/src/components/shell/WorkspaceShell.module.css`
- mutable surface: `docs/tasks/recommendation-detail-score-audit-disclosure-v1/`

## Invariants

- No recommendation score weight changes.
- No benchmark, portfolio position, outcome, paper validation, or broker/order mutation.
- Keep existing recommendation API shape and route URL.
- Investor-facing copy must avoid `pipeline`, `runner`, `artifact`, raw DB field names, and English-only internal status codes in visible summary areas.

## Verification

- verification command: `cd apps/web && npm test -- --run src/components/recommendation-score-audit-panel.test.tsx`
- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-score-audit-disclosure-v1`
- verification command: Browser QA on `http://127.0.0.1:13000/recommendations/recommendation-471` at 375px, 768px, and 1280px.

## Acceptance Criteria

- The score/outcome area starts with score, score input count, active scoring input count, explanatory input count, and outcome state.
- Detailed score cards and calculation input metadata are behind a disclosure control.
- The route keeps real order submission blocked and does not mutate recommendation results.
- The visible score summary is Korean and avoids raw internal operation terminology.
