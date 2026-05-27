# decision-cockpit-outcome-wait-visibility-v1 Contract

## Task Request

- request: 추천 weight를 바꾸지 못하는 성과 성숙 대기 구간을 첫 화면에서 바로 이해할 수 있게 한다.

## Goal

- goal: 홈 화면이 `/api/data-health.outcome_maturity_wait_monitor`를 사용해 추천 outcome 다음 측정일, 포트폴리오 feedback 성숙 예정일, weight 검토 차단 사유, 주문 차단 경계를 명확히 노출한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/decision-cockpit-outcome-wait-visibility-v1/*`

## Invariants

- Do not change recommendation scoring weights.
- Do not run or schedule calibration early.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide immature outcome state as healthy evidence. It must remain visible as managed wait.

## Scope

- Add a concise Korean home section explaining why manual/automatic weight review is blocked now.
- Surface recommendation outcome due date and portfolio feedback maturity date.
- Link deeper investigation to `/data-health`, `/recommendations`, and `/portfolio/coverage`.
- Reuse the existing data-health DTO; do not add a new API or DB table.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task decision-cockpit-outcome-wait-visibility-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] Home page renders an outcome wait section in Korean.
- [ ] Section includes recommendation due date, portfolio feedback maturity date, weight review boundary, and order boundary.
- [ ] Local verification passes.
- [ ] EC2 route smoke confirms live rendering.
