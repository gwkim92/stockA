# live-ai-invocation-health-remediation-v1 Handoff

## Status

- completed: local implementation, GitHub push, EC2 deploy, real Codex OAuth translation smoke, and final `/api/data-health` gate check passed.

## Current Status

- completed: Reconnected to EC2 from home and restored the local tunnel at `http://127.0.0.1:13000`.
- completed: Confirmed `/api/data-health` has two open gates: `live_ai_invocation_health_attention` and `active_recommendation_price_freshness_attention`.
- completed: Confirmed latest AI health failure is `news-rss-korean-translation`, not OAuth login failure.
- completed: Confirmed root cause: document `15052` has no explicit `AI` token, but Codex OAuth translation output inferred `AI`; validator correctly rejected it.
- completed: Hardened the translation prompt and added one strict retry path after grounding validation failure.
- completed: Deployed commit `be0efd2` to EC2 and restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- completed: Ran real EC2 `news-rss-translation-run --provider codex_oauth --execute`; run `3253` updated document `15052`, invocation `4351`, failed document count `0`.
- completed: Verified `/api/data-health.open_gates` no longer includes `live_ai_invocation_health_attention`; live AI status is `recovered_with_recent_failures` because old failed invocations remain auditable while latest critical tasks succeeded.
- completed: Closed the remaining `active_recommendation_price_freshness_attention` operational gate by refreshing stale active symbols `AVGO`, `BE`, and `DG` through Twelve Data; all reached latest trade date `2026-06-03`.

## Remaining

- Watch the next scheduled news translation run to ensure the stricter prompt keeps succeeding.
- Keep old failed model invocations for audit; do not delete them.

## Exact Next Step

- exact next step: continue with the next product/UX or quality task now that `/api/data-health.open_gates` is empty; do not start `manual-weight-review-pilot-v1` before outcome maturity.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src/stockanalysis/ingest/news/translation.py tests/test_news_rss_translation.py`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task live-ai-invocation-health-remediation-v1`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_news_rss_translation`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall src/stockanalysis/ingest/news/translation.py tests/test_news_rss_translation.py`
- passed on EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service` returned `active active`.
- passed on EC2: `news-rss-translation-run --provider codex_oauth --execute` returned `run_id=3253`, `updated_document_count=1`, `failed_document_count=0`, `document_id=15052`, `invocation_id=4351`.
- passed on EC2: `market-price-free-backfill-run` for `AVGO`, `BE`, `DG` returned `succeeded_symbol_count=3`, `failed_symbol_count=0`, `provider_request_count=3`, latest trade date `2026-06-03`.
- passed on EC2: `/api/data-health.open_gates=[]`, `live_ai_invocation_health.attention_required=false`, `active_recommendation_price_freshness.status=fresh`.

## Boundaries

- Recommendation scoring weights are unchanged.
- Broker/live order submit remains blocked.
- Failed model invocation history is retained for audit.
