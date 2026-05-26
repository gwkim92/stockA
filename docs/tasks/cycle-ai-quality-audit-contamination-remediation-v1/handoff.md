# cycle-ai-quality-audit-contamination-remediation-v1 Handoff

## Status

- completed: grounding false-positive remediation, stale direct impact cleanup, duplicate title cleanup, EC2 reruns, and data-health verification are complete.
- blockers: none known yet.

## Context

- `professional-source-blocker-raw-filing-remediation-v1` completed with EROK durable exclusion.
- `news-intraday-scheduler-failure-remediation-v1` completed; `news-intraday` rerun succeeded and data-health reports `last_result=success`.
- EC2 data-health now reports `cycle_ai_quality_audit.status=ok`.
- Root cause for the first issue class: quality audit grounding was stricter than the actual news validator/enrichment policy. It missed normalized company names such as `Qorvo, Inc.`/`Workday, Inc.` and curated ETF/index aliases such as `S&P 500 -> SPY`.
- Implemented fix: `cycle_ai_quality_audit` now grounds direct impacts via normalized company-name tokens and curated ETF/index aliases; the AI validator now accepts the same curated index proxy aliases for future batch outputs.
- EC2 evidence after commit `9ca5905`: `cycle-ai-quality-audit-run --execute` wrote `/opt/stockanalysis/runtime/cycle-ai-quality-audit-2026-05-26.json` with `run_id=1619`, `issue_count=3`, `readiness_gap_count=0`, `ungrounded_direct_ticker_count=1`, `macro_false_ticker_count=1`, `duplicate_title_count=1`, `quantum_energy_mislink_count=0`.
- EC2 evidence after commit `05193ad`: `cycle-ai-stale-direct-impact-cleanup-run --execute` wrote `/opt/stockanalysis/runtime/cycle-ai-stale-direct-impact-cleanup-2026-05-26.json` with `run_id=1620`, `candidate_count=1`, `removed_count=1`; it removed stale `event_id=19`/`SPY`.
- EC2 evidence after commit `278da4a`: `cycle-ai-duplicate-title-cleanup-run --execute` wrote `/opt/stockanalysis/runtime/cycle-ai-duplicate-title-cleanup-2026-05-26.json` with `run_id=1622`, `candidate_count=1`, `deleted_event_count=1`, `deleted_document_count=1`; it removed the duplicate `SpaceX's road to landmark IPO filing` empty event/document.
- Final EC2 audit evidence: `cycle-ai-quality-audit-run --execute` wrote latest report with `run_id=1623`, `audit_status=ok`, `audit_score=100`, `issue_count=0`, `readiness_gap_count=0`, `ungrounded_direct_ticker_count=0`, `macro_false_ticker_count=0`, `duplicate_title_count=0`, `quantum_energy_mislink_count=0`.
- Before this fix, data-health showed `issue_count=12`, `readiness_gap_count=1`, `ungrounded_direct_ticker_count=8`, and `macro_false_ticker_count=3`.
- Remaining known issue classes for this task: none.

## Exact Next Step

- exact next step: move to `source-blocked-recommendation-guardrail-v1`, because `/api/data-health` still reports `professional_source_gap_attention` and EROK has an active recommendation despite a durable source blocker.

## Verification Evidence

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_news_rss_ai_extract`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_news_rss_ai_extract tests.test_data_operations_cli`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-ai-quality-audit-contamination-remediation-v1`
- EC2 compileall on commit `9ca5905`
- EC2 `cycle-ai-quality-audit-run --execute --as-of-date 2026-05-26 --lookback-days 30`
- EC2 `/api/data-health` returned the new report with `issue_count=3`.
- Route smoke: `/`, `/data-health`, `/stocks/EROK` returned `200`.
- EC2 stale direct impact cleanup `run_id=1620`: `candidate_count=1`, `removed_count=1`.
- EC2 duplicate title cleanup `run_id=1622`: `candidate_count=1`, `deleted_event_count=1`, `deleted_document_count=1`.
- EC2 final quality audit `run_id=1623`: `audit_status=ok`, `audit_score=100`, `issue_count=0`.
- EC2 `/api/data-health` returned `cycle_ai_quality_audit.status=ok`.
- Route smoke: `/`, `/data-health`, `/intelligence`, `/stocks/EROK` returned `200`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not suppress warnings without fixing or reclassifying the underlying cause.
