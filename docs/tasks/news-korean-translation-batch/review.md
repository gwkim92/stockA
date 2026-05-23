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

## Risks

- Existing EC2 data must receive the new migration before the new fields can be read.
- Old cluster artifacts will continue to lack embedded translation fields until cluster evidence is rerun after translations are stored.
- Translation quality depends on Codex OAuth runtime availability; failure is recorded in `ops.pipeline_run` and `ai.model_invocation`, and the frontend falls back to deterministic labels.
