# decision-surface-language-density-v1 Contract

## Task Request

- request: 남은 핵심 투자 판단 화면의 UX/UI 문구와 첫 화면 밀도를 계속 정리한다.
- context: 이전 `investor-facing-copy-boundary-v1`은 내부 처리 설명을 제거했다. 다음 문제는 `/cycles`, `/paper-trading`, `/portfolio/coverage`, 추천 상세 일부가 여전히 설명문이 길고 “무엇을 먼저 봐야 하는지”가 약한 것이다.

## Goal

- goal: 주요 판단 화면이 `지금 결론`, `확인할 위험`, `다음 행동` 중심으로 읽히며, 반복적인 방어 문구와 내부 용어 노출을 줄인다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/performance/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/decision-surface-language-density-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide blocked state, source limitations, immature outcome windows, or read-only order boundary.
- Keep operational/debug wording in `/data-health` and `/admin/ai-agents` out of scope.

## Scope

- Tighten first-screen copy and command-card wording.
- Replace repeated “this is not an order screen” style copy with concise execution boundary language.
- Keep current data, links, and evidence sections intact.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-surface-language-density-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/cycles` leads with the cycle risk to inspect, not a process explanation.
- [ ] `/paper-trading` clearly separates simulated review, blocked execution, and actual submitted orders.
- [ ] `/portfolio/coverage` leads with portfolio risk gaps and maturity boundary, not operational detail.
- [ ] Recommendation detail panel uses investment-evidence language rather than internal AI/process wording.
- [ ] Local verification passes.
