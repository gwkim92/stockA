# news-translation-grounding-guard Review

## Result

- Root cause found at the data boundary: `document_id=22` had a correct English source title but a stored Korean title/summary for an unrelated SpaceX/Starlink article.
- The translation batch previously accepted schema-valid Codex OAuth output without checking whether English entities were grounded in the source input.
- The fix blocks ungrounded Latin tokens before recording a successful translation invocation or updating the source document.
- The dashboard scheduler status mismatch was also fixed by reading the existing EC2 profile scheduler status report.
- EC2 was updated to commit `1cbee92`, `document_id=22` was retranslated by Codex OAuth, and the latest MACRO_RATES_FED cluster artifact now shows the corrected Dow/Tesla/Iran Korean translation.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 841 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-translation-grounding-guard`: passed.
- EC2 targeted tests and compile: passed.
- EC2 API smoke: `/api/dashboard/today` returns `scheduler=installed`; `/api/ai/news-clusters?limit=1` returns corrected event/source document title for `event-19`.
- Browser smoke: `/ai-evidence/ai-evidence-358` shows corrected translation and no old SpaceX/Starlink mismatch.

## Risk

- The grounding guard is intentionally conservative. Some valid translations that add explanatory English acronyms not present in the RSS input may fail and remain untranslated rather than risking polluted titles.
- This task fixed the confirmed polluted row. It did not run a full historical translation pollution scan across every RSS document.
