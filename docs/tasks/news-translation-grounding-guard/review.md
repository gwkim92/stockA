# news-translation-grounding-guard Review

## Result

- Root cause found at the data boundary: `document_id=22` had a correct English source title but a stored Korean title/summary for an unrelated SpaceX/Starlink article.
- The translation batch previously accepted schema-valid Codex OAuth output without checking whether English entities were grounded in the source input.
- The fix blocks ungrounded Latin tokens before recording a successful translation invocation or updating the source document.
- The dashboard scheduler status mismatch was also fixed by reading the existing EC2 profile scheduler status report.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 841 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-translation-grounding-guard`: passed.

## Risk

- The grounding guard is intentionally conservative. Some valid translations that add explanatory English acronyms not present in the RSS input may fail and remain untranslated rather than risking polluted titles.
- Existing polluted rows still need runtime cleanup on EC2 after deployment.
