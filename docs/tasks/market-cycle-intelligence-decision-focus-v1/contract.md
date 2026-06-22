# market-cycle-intelligence-decision-focus-v1 Contract

## Task Request

- request: `/intelligence`, `/cycle-map`, `/market-map`를 오늘 볼 흐름과 추천 영향 중심으로 정리한다.
- context: 이전 UX 패스는 추천/종목/근거 상세 문구를 투자자용으로 정리했다. 남은 핵심 흐름 화면은 아직 `뉴스·AI`, `이 화면은`, `자동 매수 신호`, `AI가 즉석에서` 같은 내부/방어형 표현이 남아 있다.

## Goal

- goal: 뉴스, 사이클, 시장 지표 화면이 `오늘 먼저 볼 것`, `왜 중요한가`, `어느 종목/추천에 이어지는가`, `무엇을 보류해야 하는가`를 첫 화면에서 명확히 보여준다.

## Mutable Surface

- mutable surface: `apps/web/src/app/intelligence/page.tsx`
- mutable surface: `apps/web/src/app/cycle-map/page.tsx`
- mutable surface: `apps/web/src/app/market-map/page.tsx`
- mutable surface: `docs/tasks/market-cycle-intelligence-decision-focus-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide source limitations, stale indicators, blocked evidence, or read-only order boundary.
- Keep operational/debug wording in `/data-health` and `/admin/ai-agents` out of scope.

## Scope

- Replace internal/process copy with investor-facing decision copy.
- Tighten hero and major section language.
- Keep existing data, links, cards, route structure, and CSS classes intact.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-decision-focus-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/intelligence` no longer leads with `뉴스·AI` or screen-defense copy.
- [ ] `/cycle-map` describes cycle reading as a decision map without `자동 매수 신호` or AI-process wording.
- [ ] `/market-map` labels the main lane as market readout/checkpoints rather than generic process sequence.
- [ ] Local verification passes.
