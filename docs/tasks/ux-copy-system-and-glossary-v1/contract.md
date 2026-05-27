# ux-copy-system-and-glossary-v1 Contract

## Task Request

- request: audit에서 확인된 사용자 화면의 개발자 용어와 오해되는 “사람 검토” 문구를 먼저 정리한다.

## Goal

- goal: 주요 투자 판단 화면에서 `weight`, `broker submit`, `runner`, `artifact`, `validator`, `taxonomy`, `Codex OAuth`, `사람이 검토` 같은 내부 구현어가 사용자의 판단을 방해하지 않도록 한국어 투자/운영 용어로 바꾼다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/remediation/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/ux-copy-system-and-glossary-v1/*`

## Invariants

- Do not change backend DTO shape.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, broker/order flow, live trading, or paper execution.
- Do not hide warnings, blockers, source limits, or read-only order boundaries.

## Scope

- Copy-only refactor for high-frequency internal terms.
- Preserve technical IDs where they are explicitly operational details, but label them as records rather than user actions.
- Keep this slice small. Page layout redesign happens in later tasks.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ux-copy-system-and-glossary-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] Key audited pages no longer expose the most obvious English developer terms in primary copy.
- [x] “사람이 검토” copy is replaced where no actual human review action exists.
- [x] Local frontend verification passes.
