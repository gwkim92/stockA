# Review

## Review Notes

- Added a preview-first `stockanalysis-operations manual-local-ingest-smoke` CLI.
- Planned jobs are `market-price-daily`, `news-rss-daily`, and `event-intelligence-weekly`.
- Default mode is `preview_not_executed`; provider/API/DB writes require `--execute`.
- Execute mode delegates to the existing artifact runner and aggregates stdout/stderr/metadata paths.
- Runtime venv Python is preferred when present to avoid the known default Python 3.14 runtime issue.
- Env values are not emitted; tests cover DB password/API token redaction.
- No `launchctl`, LaunchAgents write/delete, external scheduler deployment, schema change, DTO change, or broker/order behavior was performed.

## Verification Evidence

- `bash scripts/verify_manual_local_ingest_smoke.sh`: pass.
- `bash scripts/verify_project_execution_roadmap.sh`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task manual-local-ingest-smoke`: pass.
- `git diff --check`: pass.
- Manual preview emitted `smoke_status=preview_not_executed`, `runtime_status=ready`, `python_executable=/private/tmp/stockanalysis-runtime/venv/bin/python`, and three planned jobs.
