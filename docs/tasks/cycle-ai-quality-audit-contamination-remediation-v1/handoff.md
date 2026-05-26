# cycle-ai-quality-audit-contamination-remediation-v1 Handoff

## Status

- in progress: first grounding false-positive remediation is implemented, pushed, deployed to EC2, and audit-rerun verified. The task is not fully green because one stale direct ticker impact and one duplicate title issue remain.
- blockers: none known yet.

## Context

- `professional-source-blocker-raw-filing-remediation-v1` completed with EROK durable exclusion.
- `news-intraday-scheduler-failure-remediation-v1` completed; `news-intraday` rerun succeeded and data-health reports `last_result=success`.
- EC2 data-health still reports `cycle_ai_quality_audit.status=attention_required`, but the issue count is reduced.
- Root cause for the first issue class: quality audit grounding was stricter than the actual news validator/enrichment policy. It missed normalized company names such as `Qorvo, Inc.`/`Workday, Inc.` and curated ETF/index aliases such as `S&P 500 -> SPY`.
- Implemented fix: `cycle_ai_quality_audit` now grounds direct impacts via normalized company-name tokens and curated ETF/index aliases; the AI validator now accepts the same curated index proxy aliases for future batch outputs.
- EC2 evidence after commit `9ca5905`: `cycle-ai-quality-audit-run --execute` wrote `/opt/stockanalysis/runtime/cycle-ai-quality-audit-2026-05-26.json` with `run_id=1619`, `issue_count=3`, `readiness_gap_count=0`, `ungrounded_direct_ticker_count=1`, `macro_false_ticker_count=1`, `duplicate_title_count=1`, `quantum_energy_mislink_count=0`.
- Before this fix, data-health showed `issue_count=12`, `readiness_gap_count=1`, `ungrounded_direct_ticker_count=8`, and `macro_false_ticker_count=3`.
- Remaining known issue classes: stale `SPY` direct impact on `event_id=19`, because older AI/rule evidence referred to S&P 500/Treasury-yield text while the current source document title is `Dow Jones Futures Rise But Pare Gains On Mixed Iran News; Marvell, Dell Jump Before Earnings`; duplicate title `spacex's road to landmark ipo filing`.

## Exact Next Step

- exact next step: add a deterministic stale-impact cleanup for direct instrument impacts whose current linked source text no longer grounds the ticker or curated alias, starting with `event_id=19`/`SPY`; then address the remaining duplicate title issue.

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

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not suppress warnings without fixing or reclassifying the underlying cause.
