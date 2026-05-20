# Frontend Audit Metadata Disclosure Plan

## Goal

- 사용자 화면의 첫 시선에서는 의미 있는 근거와 링크를 보여주고, 감사용 raw ID는 접힌 metadata로 낮춘다.
- `performance-outcome-*`, `market-feature-*`, `universe-rank-*`, `pipeline-run-*` 같은 내부 ID는 삭제하지 않고 필요할 때 펼쳐 볼 수 있게 한다.

## Scope

- 포함:
  - reusable audit metadata disclosure component
  - thesis detail evidence cards
  - recommendation score component cards
  - CSS for long metadata wrapping
  - docs task records
- 제외:
  - backend DTO changes
  - database/schema changes
  - scoring/recommendation logic
  - AI/RAG generation
  - broker/order/scheduler behavior

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/theses/AAPL-bootstrap-v1`
- browser smoke for `/recommendations/AAPL-2024-11-01`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-audit-metadata-disclosure`
- `git diff --check`
