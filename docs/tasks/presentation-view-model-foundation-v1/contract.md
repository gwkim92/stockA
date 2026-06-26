# presentation-view-model-foundation-v1 Contract

## Request

- 투자자 화면의 visible copy를 raw DTO와 사후 `replaceAll` 변환에서 분리한다.

## Scope

- Add frontend-only view models under `apps/web/src/lib/presentation/`.
- Cover recommendation detail, stock detail, portfolio coverage, paper trading, and operations overview copy.
- Add unit tests for key status/code mappings.

## Invariants

- Do not change backend DTOs.
- Do not change score, schema, benchmark, portfolio positions, broker/order flow, or AI analysis logic.
- `investorCopy()` remains as legacy compatibility only.

## Verification

- `cd apps/web && npm test`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task presentation-view-model-foundation-v1`
