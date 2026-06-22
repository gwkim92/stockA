# market-cycle-intelligence-visual-hierarchy-v1 Contract

## Task Request

- request: `/intelligence`, `/cycle-map`, `/market-map`의 반복 카드 그리드와 시각적 위계를 개선한다.
- context: 이전 `market-cycle-intelligence-decision-focus-v1`은 문구를 정리했다. 남은 문제는 세 화면의 상단 카드와 주요 그리드가 같은 크기와 리듬으로 반복되어 무엇을 먼저 봐야 하는지 약하다는 점이다.

## Goal

- goal: 데스크톱에서 핵심 카드가 더 크게 보이는 비대칭 리서치 데스크 레이아웃을 적용해 첫 시선이 `오늘 먼저 볼 것`으로 향하게 한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/intelligence/page.tsx`
- mutable surface: `apps/web/src/app/cycle-map/page.tsx`
- mutable surface: `apps/web/src/app/market-map/page.tsx`
- mutable surface: `apps/web/src/app/globals.css`
- mutable surface: `docs/tasks/market-cycle-intelligence-visual-hierarchy-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide stale data, blocked evidence, source limitations, or read-only order boundary.
- Keep mobile/tablet layout safe; desktop-only visual hierarchy changes are preferred.

## Scope

- Add page-specific root/hero classes.
- Add desktop-only asymmetric grid styling for command cards and key evidence/pressure cards.
- Keep existing links, data, route structure, and component behavior intact.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-visual-hierarchy-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/intelligence` command cards and evidence flow are no longer uniform equal-card blocks on desktop.
- [ ] `/cycle-map` first cycle focus and path board have stronger visual hierarchy on desktop.
- [ ] `/market-map` quality/pressure/regime/boundary cards read as a checkpoint board, not a generic 4-card row.
- [ ] Local verification passes.
