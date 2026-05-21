# Review Notes

## Summary

- Root cause: after DB reset/recovery, the latest `news-intraday` profile only ran `news-rss-ai-extract-run`; local-rule `news-rss-cluster-evidence-run` was no longer part of the automatic profile.
- Fix: restore `news-cluster-evidence` before `news-ai-evidence` in the `news-intraday` operating-data profile.
- Operator guidance now points manual news intelligence execution at the same profile-level command, not a partial AI-only runner.
- EC2 live data now has news clusters again: 4 `news_cluster_summary` artifacts and 19 `news_event_candidate` artifacts.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract -v`: pass, 28 tests.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-cluster-automation-regression`: pass.
- EC2 API smoke: `/api/ai/news-clusters?asOfDate=2026-05-21&limit=4` returned `cluster_count=4`, `clustered_event_count=26`.
- Tunnel web smoke: `/intelligence` rendered news evidence and cluster markers.

## Remaining Risks

- Manual EC2 profile execution wrote DB rows successfully but failed at final report file write because the existing scheduler report file was root-owned. Ownership was corrected; the next timer run should refresh the report file normally.
- This slice does not change scoring, recommendation generation, or broker/order flow.
