# data-health-decision-gate-redesign-v2 Contract

## Task Request

- request: `/data-health`가 운영자 로그처럼 보이고 사용자가 무엇을 먼저 봐야 하는지 알기 어렵다. 기본 화면은 판단 게이트 중심으로 줄이고, 세부 실행·성과·전문 분석 상태는 접힌 상세 영역으로 분리한다.

## Goal

- goal: `/data-health` 첫 화면에서 “현재 시스템이 정상 자동 동작하는가, 수집/분석 중 무엇이 문제인가, 추천 판단 전에 무엇을 확인해야 하는가”를 빠르게 판단할 수 있게 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/tasks/data-health-decision-gate-redesign-v2/*`

## Invariants

- Do not change backend DTO shape.
- Do not change DB schema, scheduler behavior, or data operation cadence.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide warnings, blockers, source limits, or read-only order boundaries.

## Scope

- Reduce default top-level decision cards to the essential user-facing set.
- Move secondary portfolio/professional/outcome detail cards into a collapsed detail section.
- Move collection/analysis status near the top so the page answers “what is being collected and analyzed?” first.
- Replace prominent internal wording in the default path with user-facing Korean labels.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-decision-gate-redesign-v2`

## Done Criteria

- [x] `/data-health` default path shows a small set of priority status cards.
- [x] Collection/analysis status appears before long operational details.
- [x] Secondary status cards remain reachable but are not dumped into the first screen.
- [x] Local frontend verification passes.
- [x] EC2 and local tunnel route smoke pass.
