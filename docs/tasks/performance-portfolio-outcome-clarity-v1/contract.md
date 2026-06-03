# performance-portfolio-outcome-clarity-v1 Contract

## Task Request

- request: `/performance`와 `/portfolio/coverage` 화면의 UX 문구를 정리해 성과 측정, 보유 상태, 리스크 예산, 가상 매매/실거래 차단 상태를 사용자 관점에서 이해 가능하게 만든다.

## Goal

- goal: 성과 화면과 포트폴리오 보유 화면이 운영자 로그나 수동 검토 UI처럼 보이지 않고, 사용자가 “성과를 믿어도 되는지”, “보유 종목에서 무엇을 확인해야 하는지”, “왜 주문과 추천 산식 변경이 막혀 있는지”를 바로 알 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/performance/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `docs/tasks/performance-portfolio-outcome-clarity-v1/*`

## Invariants

- Do not change API contracts.
- Do not change recommendation scoring weights.
- Do not change benchmark definitions, portfolio positions, performance outcomes, paper validation records, broker/order flow, live trading, or scheduler cadence.
- Do not add write actions, order buttons, calibration execution, or manual review controls.
- Keep this task as frontend visibility and UX copy only.

## Scope

- Replace ambiguous “검토” wording where it implies a missing human workflow with clearer status/readout wording.
- Rename `/portfolio/coverage` page intent from “보유 검토” to “보유·리스크 상태”.
- Make performance evaluation copy distinguish measured outcome, holding-state comparison, and scoring-weight lock.
- Preserve existing page sections and data layout unless a small wording adjustment is needed for clarity.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task performance-portfolio-outcome-clarity-v1`
- verification command: `git diff --check`

## Done Criteria

- [x] `/performance` no longer says “보유 검토” for holding-state comparisons.
- [x] `/portfolio/coverage` uses “보유·리스크 상태”, “확인 대상”, “상태”, and “다음 확인” instead of ambiguous manual-review copy.
- [x] The pages keep the read-only/no-order/no-weight-change boundary explicit.
- [x] Local frontend/backend verification passes.
- [x] EC2 route smoke confirms the updated Korean copy renders.
