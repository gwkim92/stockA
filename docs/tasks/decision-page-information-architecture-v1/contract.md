# decision-page-information-architecture-v1 Contract

## Task Request

- request: 주요 판단 화면의 중복 섹션을 줄이고 투자자가 읽는 순서를 더 명확하게 만든다.
- context: `market-cycle-intelligence-visual-hierarchy-v1`은 카드 크기와 시각 위계를 개선했다. 남은 문제는 일부 화면이 같은 의미를 여러 섹션에서 반복하고, “무엇을 먼저 봐야 하는지”가 아직 길게 읽어야 보인다는 점이다.

## Goal

- goal: `/intelligence`, `/cycle-map`, `/market-map`의 정보 구조를 `핵심 변화 → 근거 → 연결 대상 → 보류/차단 경계` 순서로 정리한다.

## Mutable Surface

- mutable surface: `apps/web/src/app/intelligence/page.tsx`
- mutable surface: `apps/web/src/app/cycle-map/page.tsx`
- mutable surface: `apps/web/src/app/market-map/page.tsx`
- mutable surface: `apps/web/src/app/globals.css`
- mutable surface: `docs/tasks/decision-page-information-architecture-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide stale data, blocked evidence, source limitations, quality flags, or read-only order boundary.
- Keep existing route links valid.
- Keep Korean user-facing wording focused on investment judgment, not implementation details.

## Scope

- Reduce repeated summary sections.
- Combine related queue/status cards where the user needs one decision checkpoint.
- Keep all core paths available: source news, evidence candidates, blocked evidence, recommendations, cycle layers, market correlations, market pressure, data health.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-page-information-architecture-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/intelligence` has one clear triage section for representative evidence, blocked items, and recommendation linkage.
- [ ] `/cycle-map` no longer repeats the same attention-node summary in adjacent sections.
- [ ] `/market-map` no longer repeats hero/readout/checkpoint summaries before the actual correlation/pressure data.
- [ ] Local verification passes.
