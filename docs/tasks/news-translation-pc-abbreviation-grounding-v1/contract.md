# news-translation-pc-abbreviation-grounding-v1 Contract

## Task Request

- request: Fix recurring `news-rss-korean-translation` failures where a grounded `personal computers` source phrase is translated as `PC`.
- context: EC2 `/api/data-health` opened `live_ai_invocation_health_attention`; latest failed critical task was `news-rss-korean-translation` for `document_id=14457`, error `ungrounded latin token(s): pc`.

## Goal

- goal: Keep the translation grounding guard strict against invented English entities while allowing the common, source-grounded abbreviation `PC` when the bounded source text contains `personal computer(s)`.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/news/translation.py`
  - `tests/test_news_rss_translation.py`
  - `docs/tasks/news-translation-pc-abbreviation-grounding-v1/*`

## Invariants

- Do not allow ungrounded company names, tickers, products, or market entities.
- Do not delete failed invocation history.
- Do not change recommendation score weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Add a narrow alias expansion: `personal computer(s)` source context permits `pc` and `pcs` in Korean translation output.
- Add a regression test using the EC2 failure title.
- Re-run the failed translation path after deploy and verify live AI health closes.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: EC2 `news-rss-translation-run --provider codex_oauth --execute` smoke
- verification command: EC2 `/api/data-health` smoke
