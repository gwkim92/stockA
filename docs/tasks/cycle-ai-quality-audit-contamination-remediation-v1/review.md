# cycle-ai-quality-audit-contamination-remediation-v1 Review

## Review Summary

- Partial pass. The first contamination class was mostly false-positive audit grounding, not bad AI output. The grounding policy is now aligned across the AI validator and quality audit, and EC2 data-health shows a reduced issue count.

## Issues Found

- `cycle_ai_quality_audit` was using a naive direct ticker grounding check: raw ticker text or the first raw instrument-name token only.
- That missed legitimate direct references where the source text used a company name with punctuation (`Qorvo`, `Workday`) or an accepted ETF/index proxy (`S&P 500 -> SPY`).
- After the fix and EC2 rerun, issue count dropped from `12` to `3`.
- Remaining true issue: `event_id=19` still links `SPY` even though the current source title is a Dow Jones/Marvell/Dell headline and no longer grounds `SPY` or `S&P 500`.
- Remaining duplicate issue: title `spacex's road to landmark ipo filing` appears twice.

## Residual Risks

- `cycle_ai_quality_audit.status` is still `attention_required`; this task is not fully complete.
- The current fix does not remove stale historical impacts. It only stops counting legitimate grounded names and curated ETF/index aliases as contamination.
- A separate stale-impact cleanup is needed for event/source content drift.
- Recommendation weights remain unchanged and broker/order flow remains read-only.

## Verification Evidence

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_news_rss_ai_extract`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit tests.test_news_rss_ai_extract tests.test_data_operations_cli`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-ai-quality-audit-contamination-remediation-v1`
- EC2 commit `9ca5905`, compileall passed.
- EC2 audit rerun `run_id=1619`: `issue_count=3`, `readiness_gap_count=0`, `ungrounded_direct_ticker_count=1`, `macro_false_ticker_count=1`, `duplicate_title_count=1`, `quantum_energy_mislink_count=0`.
- EC2 `/api/data-health` reads the updated latest report.
