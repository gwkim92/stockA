# Review: news-korean-translation-batch

## Result

- The UI no longer needs to invent generic Korean text when persisted translations exist.
- RSS source documents now have canonical Korean translation fields with confidence and model invocation traceability.
- The news intraday automation plan now translates RSS documents before cluster/evidence pages consume them.

## Checks

- Unit tests cover:
  - translation candidate SQL
  - update SQL persistence
  - output validation
  - Codex OAuth prompt/schema requirements
  - provider response parsing
  - runner update/invocation behavior
  - operations CLI wiring
  - operating-data profile ordering
  - cadence registry entry
- Existing frontend live adapter tests still pass.
- Next typecheck/build still pass.
- EC2 smoke passed:
  - migration `0016_news_document_translation.sql` applied.
  - `news-rss-translation-run` stored three Codex OAuth Korean translations.
  - `news-rss-cluster-evidence-run` regenerated four cluster artifacts after translation.
  - FastAPI and Next.js services restarted and returned 200 for the checked pages.
  - Data-health reports `news-korean-translation-intraday` and `event-intelligence-weekly` as `ok`.

## Risks

- Only the first three EC2 documents were translated in the smoke run. Remaining RSS documents will be translated by subsequent batch runs.
- Old cluster artifacts will continue to lack embedded translation fields until cluster evidence is rerun after translations are stored; the latest smoke produced new translated artifacts for current top clusters.
- Translation quality depends on Codex OAuth runtime availability; failure is recorded in `ops.pipeline_run` and `ai.model_invocation`, and the frontend falls back to deterministic labels.
