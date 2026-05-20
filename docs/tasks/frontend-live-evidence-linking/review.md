# Frontend Live Evidence Linking Review

## Verification

- Focused backend test passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- Frontend checks passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
- Live API smoke passed:
  - `/api/events?asOfDate=2024-11-01` returned AAPL / `ANNUAL_REPORTING` / `ai-evidence-1` for event rows.
  - `/api/source-documents/source-document-0000320193-24-000123` returned AAPL and linked evidence `ai-evidence-1`.
  - `/api/ai-evidence/ai-evidence-1` returned AAPL and `ANNUAL_REPORTING`.
- Browser smoke passed:
  - `/events` renders AAPL / `ANNUAL_REPORTING` / AI evidence links.
  - `/source-documents/source-document-0000320193-24-000123` renders AAPL and linked evidence.
  - `/ai-evidence/ai-evidence-1` renders AAPL, annual filing classification, Codex OAuth run metadata, and source chunk.
- Diff hygiene passed:
  - `git diff --check`

## Residual Risks

- AI extracted fields are still sparse because the current local Codex OAuth smoke produced minimal structured output. This task fixed visibility, not extraction quality.
- Source document detail exposes local storage URI and checksum in local MVP mode. Production redaction policy should be handled before public deployment.
