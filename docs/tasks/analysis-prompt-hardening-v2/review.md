# SEC and Codex news hardening — review

## Implemented changes

### SEC numeric and final candidate boundary

The baseline SEC parser accepted NaN confidence, boolean confidence as 1, and numeric strings by coercion. The unchanged EVENT_OUTPUT_SCHEMA is now enforced before conversion. Actual finite JSON numbers in [0,1] are required for confidence and significance. Required fields, timezone-aware event timestamps and undeclared fields are also checked. Duplicate JSON keys, non-finite JSON tokens and overflow numbers are refused in the decoding paths, while the existing fenced-JSON compatibility is retained.

The canonical candidate builder validates the typed provider result again. An injected provider cannot bypass the parser to insert an invalid event. Invalid threshold/budget inputs are rejected before database/provider access. The existing minimum confidence remains 0.8; zero stays a measured zero and still fails that unchanged acceptance threshold. Valid empty time_horizon/impact_polarity strings survive parse -> artifact -> candidate round trips rather than becoming null and failing the second validation.

The SEC prompt also checks that source and chunk IDs are the same positive integer. This is an identity-consistency check, not proof that the text belongs to a real filing. Its raw source framing, leading-text chunk selection and semantic date/event/source entailment are not comprehensively redesigned here.

### Separate Codex translation and news prompts

Both builders now use the versioned common source-data rules already introduced by PR #35. Original metadata, raw text, retrieval context and prior validation errors are escaped and framed as source_data. They are not concatenated as new trusted instructions. The complete escaped/framed source section must fit the existing role input cap; it is not silently cut as serialized JSON. This bound is not a total prompt/token bound, and existing leading-text chunk helpers still have their separate selection behavior.

Translation retains faithful-title/summary guidance, negation, uncertainty and identifier rules. Prior validation errors are data inside the framed input; the retry instruction itself is static. Its parser now enforces the existing schema, including finite typed confidence. The pipeline's existing grounding entrypoint checks typed provider outputs again before updating translated text. Empty translation wrappers cannot fall through to unrelated sibling fields.

News structuring now asks for Korean explanations but exact original-language evidence spans from the actual RSS title or summary. Classification metadata, current_event_impacts and similar articles remain contextual hypotheses rather than original quotations or direct company proof. The prompt no longer permits translated/paraphrased text as a quote. Unsupported impact lists may remain empty.

Literal spans are checked against either original source field after whitespace normalization. SDK and Codex providers enforce the same check, and the pipeline repeats it for injected providers before recording successful model output or inserting extraction/impact records. A metadata-only label, invented sentence or translated paraphrase is not substituted for an original span. Valid literal text still reaches the existing canonical review path. Empty span collections remain allowed by the unchanged schema.

News confidence, impact strength, causal-path confidence and configured minimum confidence reject non-finite, boolean, string or out-of-range values rather than coercing/clamping them. Legacy instrument_impacts fields remain supported; this PR does not claim the permissive legacy parser is a complete strict-schema implementation. The existing direct-company source gate already used the original title/summary in the actual runner. A new integration test protects that behavior; it is not falsely described as a newly implemented entity-grounding algorithm.

## Versions and preserved behavior

- SEC template: 2026-09-06-sec-scalar-contract-v2.
- Codex translation template: 2026-09-06-ko-source-contract-v3.
- News structuring template: 2026-09-06-news-source-contract-v4.

Output schemas, stored artifact types, event taxonomy, financial scoring, confidence thresholds, provider/model choice, CLI permissions and fallback status conventions are unchanged. Version changes may cause the existing template/request deduplication system to reconsider older records after an eventual rollout. No template registration, ingestion run or deployment was executed here.

No SQL builder function body changed in the three edited runtime files; no migration/seed/schema, golden fixture, benchmark split, weight, portfolio/order/broker, account/secret/AWS or scheduler change is included. Existing golden news evaluation remains in regression. The only edited pre-existing test assertion updates the intentionally changed Korean-explanation wording and adds the original-language quote requirement; no test was disabled.

## Not completed / not proven

The equity file upload was denied twice with undetermined security status. Its prepared local changes were not applied through another path. The checked-in equity zero -> 0.35 confidence issue, non-finite clamping and weak-evidence/minimum-point/input-bound issues remain open. Its original runtime and tests are untouched in this branch.

Literal span membership does not establish entailment, causal correctness, citation completeness or truth. A quoted fragment can omit important context. Translation's older Latin-token grounding is not a proof of Korean semantic fidelity and still permits some metadata tokens. Legacy aliases and index-proxy rules remain. Timezone-aware timestamp validation does not establish a correct event date or prevent future-information leakage in every source query. Input framing is not prompt-injection immunity or OS capability enforcement.

The stricter checks can increase rejected results for old paraphrased spans, malformed values and oversized inputs. Current-workload rejection rate, live model accuracy, held-out semantic evaluation, source truth, complete backend regression and investment outcomes are unverified. No live model/DB/production request was made. The browser UI was not changed, and earlier UI test counts do not apply to this backend task.
