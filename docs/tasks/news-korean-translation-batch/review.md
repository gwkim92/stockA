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
  - Additional Codex OAuth batches stored 120 more Korean translations: `run_id=520` 20건, `run_id=521` 50건, `run_id=523` 50건, all with 0 failures.
  - Final Codex OAuth batches stored the remaining 113 Korean translations: `run_id=525` 50건, `run_id=526` 50건, `run_id=527` 13건, all with 0 failures.
  - `news-rss-cluster-evidence-run` regenerated four cluster artifacts after translation.
  - Latest cluster regeneration `run_id=524` produced `ai-evidence-260..263`; the quantum policy cluster is now `ai-evidence-263`, has 3/3 translated representative events, and links to `QUBT` rather than energy.
  - Full cluster regeneration `run_id=529` requested 193 events, produced 20 clusters, inserted 19 new artifacts, skipped 1 existing, and failed 0.
  - FastAPI `/api/ai/news-clusters?asOfDate=2026-05-23&limit=20` verified `all_source_documents_translated=true` and `all_events_translated=true`.
  - FastAPI and Next.js services restarted and returned 200 for the checked pages.
  - Data-health reports `news-korean-translation-intraday` and `event-intelligence-weekly` as `ok`.
  - Browser smoke for `http://127.0.0.1:13000/ai-evidence/ai-evidence-263` showed persisted Korean translations for all three representative quantum news cards.

## Risks

- EC2 has 236/236 current RSS source documents translated. New RSS documents still depend on the recurring translation batch to stay Korean-first.
- Old cluster artifacts will continue to lack embedded translation fields until cluster evidence is rerun after translations are stored; the latest smoke produced new translated artifacts for current top clusters.
- Translation quality depends on Codex OAuth runtime availability; failure is recorded in `ops.pipeline_run` and `ai.model_invocation`, and the frontend falls back to deterministic labels.
- Some non-source-document event cards can still fall back to deterministic labels when no source document translation exists; the evidence neighborhood source-document path now carries translations, but pure synthetic event titles still need separate Korean naming policy.
