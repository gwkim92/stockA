# frontend-operating-ui-qa-hardening

## Goal

EC2 운영 화면 QA에서 확인된 주요 UI/문구/상태 표현 결함을 1차로 수정한다. 목적은 서버 기능 추가가 아니라, 이미 수집된 운영 데이터가 투자자가 이해할 수 있는 한국어 화면으로 안전하게 보이게 하는 것이다.

## Scope

- Fix unreadable data-health layout caused by narrow grids and long values.
- Normalize user-facing labels for recommendation actions, outcome states, scheduler states, trading blockers, and internal reason codes.
- Reduce raw internal implementation strings in stock, recommendation, trading, remediation, and thesis screens.
- Distinguish missing data / not-yet-measured states from actual failure states.
- Improve consistency between home automation status and data-health automation status.
- Keep changes inside Next.js frontend presentation/data interpretation unless a narrow read adapter fix is required.

## Non-Goals

- No DB schema changes.
- No scoring formula changes.
- No broker/order execution changes.
- No paid external API or new RAG/vector service.
- No scheduler deployment changes.

## Acceptance Criteria

- `apps/web` renders the checked pages without obvious broken/vertical text.
- Internal strings such as `accumulate candidate`, `unmeasured`, `not requested`, `sensitivity=`, `exposure=`, and skipped reason codes are mapped or hidden from primary user-facing copy.
- Empty performance/cycle/coverage states explain whether the state is missing data, not due yet, or real failure.
- `npm run typecheck` and `npm run build` pass for `apps/web`.
- Browser QA is rerun against the active local/EC2 route where feasible.

## Evidence Source

- QA report: `dogfood-output/macro-flow-ui/report.md`
- Key screenshots: `dogfood-output/macro-flow-ui/screenshots/`
