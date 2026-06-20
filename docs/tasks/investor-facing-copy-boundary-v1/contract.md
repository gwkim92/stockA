# investor-facing-copy-boundary-v1 Contract

## Task Request

- request: 사용자 화면에 내부 처리 방식과 에이전트 작업 방식을 설명하는 문구가 노출되지 않게 정리한다.
- context: 홈, 인텔리전스, 뉴스 근거 화면에 `처리 순서`, `AI가 한 일`, `구조화`, `자동 검증` 같은 운영자/개발자 관점 문구가 투자자용 문맥으로 섞여 있다.

## Goal

- goal: 투자자용 화면은 결론, 근거, 위험, 다음 행동을 중심으로 읽히고, 내부 파이프라인 설명은 `/data-health` 같은 운영자 화면으로만 격리한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `docs/tasks/investor-facing-copy-boundary-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide data quality, AI failure, blocked evidence, or order-block state.
- Keep operational details available through operations/data-health surfaces.

## Scope

- Replace investor-facing copy that explains internal processing with copy that explains investment judgment.
- Keep navigation to source news, evidence details, blocked evidence, cycle map, recommendations, and data-health.
- Preserve all current data values and links.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task investor-facing-copy-boundary-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Home page no longer explains the system's internal work sequence as the primary user message.
- [x] `/intelligence` frames news as investment-impact evidence rather than processing pipeline.
- [x] `/ai-evidence` frames items as investment evidence, not “AI가 한 일”.
- [x] Local verification passes.
- [x] Handoff records remaining UX surfaces that still need the same copy boundary.
