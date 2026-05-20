# Frontend Flow Wording And Market Holidays Review

## Verification

- Env readiness passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
- Holiday policy check passed:
  - input scheduler run date `2026-05-25`.
  - configured non-trading date count `10`.
  - resolved freshness target `2026-05-22`.
- Frontend checks passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
- Route smoke passed:
  - `/`
  - `/data-health`
  - `/cycles`
  - `/events`
  - `/themes/ANNUAL_REPORTING`
  - `/recommendations/AAPL-2024-11-01`
  - `/theses/AAPL-bootstrap-v1`
  - `/portfolio/coverage`
  - `/performance`
  - `/ai-evidence/ai-evidence-1`
  - `/source-documents/source-document-0000320193-24-000123`
  - `/remediation`
- Browser review:
  - Home now shows the system flow before detail tables.
  - Data Health shows pipeline/domain/freshness/scheduler labels in Korean and preserves provider budget `780/800`.
  - Events, Cycles, Recommendation, Thesis, Portfolio Coverage pages no longer expose the most visible raw English labels found during review.
- Harness and diff:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-flow-wording-and-market-holidays`
  - `git diff --check`

## Residual Risks

- The UI is understandable enough for the MVP cockpit, but several detail pages still use inline styles and should be refactored into shared presentation primitives later.
- Some raw IDs are intentionally still visible, such as `pipeline-run-*`, evidence IDs, and artifact/source run IDs, because they are audit handles.
- Holiday maintenance is manual in repo-outside env. No external exchange calendar provider is wired.
- This task does not change scoring, recommendation quality, RAG/ontology, paper trading, or real trading.
