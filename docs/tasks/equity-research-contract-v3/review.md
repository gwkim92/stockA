# Equity research correctness review

Base: develop@9c90f5f7220861a2f57d4ee7e5e5dd72d588fa83. Task: equity-research-contract-v3.

## Fixed behavior

The model confidence field no longer replaces explicit zero with 0.35 or clips values outside [0, 1] into that range. The existing research output schema is now enforced at parsing, typed-provider completion and artifact serialization. Missing confidence, bool/string/non-finite values, undeclared fields and non-string claim entries are rejected instead of coerced. Valid zero, empty optional scenario strings and empty claim lists retain their meaning.

A follow-up adversarial test exposed another typed-provider bypass: converting a string or dictionary to list could make character/key fragments appear to be valid claims. Collection types are now checked before conversion. Invalid provider results never receive a model-success invocation record; the existing explicit failed-invocation and deterministic fallback path remains. Fallback can still persist its own artifact and is not described as a successful model analysis. No live database was accessed to prove these paths: fake-executor SQL logs are inspected.

The Codex equity prompt uses the existing shared untrusted-source framing and explicitly separates source financial facts, model assumptions and previous recommendation hypotheses. It allows 0-7 supported key points rather than pressuring a minimum of three. This is instruction and data-shape hardening, not semantic entailment or injection immunity.

## Evidence selection and size

The original per-section record limits remain. The complete escaped/framed source section is checked after initial selection and the existing reduced selection. A large thesis or nested description that still cannot fit is rejected before provider/process invocation; JSON and individual source records are never sliced. Input budgets require an integer in the existing 2,000-100,000 range. This is a character cap for source data, not a total prompt-token limit.

The reporting runner establishes the bounded selection before model invocation or writes and supplies that same selection to the provider, request hash and artifact source-document metadata. Omitted source records cannot appear as considered evidence simply because they existed in the full fetched context. Selection is idempotent and labeled bounded_selection_not_complete_source_history. A changing omitted record does not change the selected-context hash; a selected record does. The metadata is an input inventory, not proof that every statement cites or follows every included source.

## Compatibility and verification

Equity prompt template version is 2026-09-06-equity-contract-v3. The task name, artifact type full_equity_research, generation/storage schema, SQL-generator bodies, models/providers, financial scoring and fallback labels remain unchanged. An AST comparison of every render_* function and the output schema builder matches the baseline exactly. The previous test that expected confidence 1.3 to be clamped now checks preservation of valid 0.93; new tests explicitly reject out-of-range confidence. No golden input, threshold or evaluation split changed.

Initial new regression tests were run against the byte-matched baseline and failed as expected, including explicit-zero corruption and overbudget/injected-provider paths. The additional typed-collection test also failed before its fix. After changes, 27 new methods plus 7 existing equity methods pass locally (34 total). The uploaded runtime blob matches the tested file. Local source came from the previous read-only archive; affected baseline blobs matched current GitHub, but this is not claimed as a complete current checkout or complete local backend run. The clean CI checkout runs the existing 159 selected tests plus these 27 on Python 3.11/3.13 with real socket/process guards enabled.

## Remaining limits

This does not prove live model accuracy, quotation entailment, causal validity, financial-number correctness, or point-in-time reconstruction. The unchanged SQL's latest-thesis query does not restrict thesis creation time to the requested cutoff; historical precision still needs explicit design and tests. Existing source-side string numeric conversion, deterministic fallback prose/default confidences, model-reported usage, title/summary/list length truncation and provider error handling remain separately scoped. The unchanged output schema has no per-claim source-reference field, so precise claim-to-source validation is not implemented by this task.

Stricter outputs and source-size checks may raise rejection rates on real workloads. Oversize context currently aborts the batch before writes, including an otherwise usable symbol in that batch; failure isolation under mixed input sizes remains a rollout consideration. No live shadow data, EC2 query, paid model call, deployment, main, dependency, schema/migration, scoring weight, benchmark, portfolio/order/broker, account/secret/AWS or scheduler change occurred. This is an offline correctness improvement, not a complete production acceptance.
