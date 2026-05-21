# Review Notes

## Summary

- Root cause: after DB reset/recovery, the latest `news-intraday` profile only ran `news-rss-ai-extract-run`; local-rule `news-rss-cluster-evidence-run` was no longer part of the automatic profile.
- Fix: restore `news-cluster-evidence` before `news-ai-evidence` in the `news-intraday` operating-data profile.
- Operator guidance now points manual news intelligence execution at the same profile-level command, not a partial AI-only runner.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract -v`: pass, 28 tests.

## Remaining Risks

- EC2 deploy and live data regeneration are pending.
