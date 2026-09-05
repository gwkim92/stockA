# Runtime prompt audit — 2026-09-06

Baseline: `develop@e6ae966d4cdd0aafd03446c3674b4eb6fd62e23f`. Integration: PR #35. This audit inspects checked-in prompt construction and parser/validator paths; it does not attest to the running EC2 configuration or live model accuracy.

## What actually runs

The repository has five task-specific runtime prompt families, plus a common Agents SDK assembly layer and 13 role definitions in `ai_agents/registry.py`. A role declaration is not evidence that an autonomous agent is deployed. Current direct callers of the common SDK executor are news translation and news structuring. No provider selection was changed in this task.

| Family | Runtime builder and downstream check | This task |
| --- | --- | --- |
| RSS Korean translation | `ingest/news/translation.py`: `build_codex_oauth_news_translation_prompt`, translation parser/grounding checks; separate common-SDK path | SDK input/output contract and dedicated faithful-translation instructions changed. Separate Codex builder inspected, not rewritten. |
| News evidence structuring | `ingest/news/ai_extract.py`: `build_codex_oauth_news_ai_prompt`, `validate_news_ai_output`, ontology validation; separate common-SDK path | SDK instructions distinguish original quotations from Korean explanations, direct company evidence from retrieved context; existing schema enforced in SDK and locally. Separate Codex builder inspected, not rewritten. |
| SEC event extraction | `ingest/sec/ai_event_extract.py`: `build_codex_oauth_event_prompt`, `parse_structured_event_output`, candidate gate | Inspected and included in deterministic regressions. Runtime unchanged; scalar-validation finding remains open below. |
| Equity research | `ai/equity_research_reporting.py`: `build_codex_oauth_equity_research_prompt`, research parser/sanitizer | Inspected and regression-tested. Runtime unchanged; zero-confidence and sparse-evidence findings remain open below. |
| Cycle community summary | `ai/cycle_community_ai_summary.py`: `build_codex_oauth_cycle_community_ai_prompt`, bounded context, response sanitizer | Prompt, exact reference binding, post-selection input bound and actual-budget fingerprint changed. Existing storage shape and financial scoring untouched. |
| Role catalog and common SDK | `ai_agents/registry.py`, `runtime_policy.py`, `agents_sdk_provider.py` | All 13 definitions read. Base registry/seed strings remain unchanged. Common SDK uses a separately versioned contract and real `AgentOutputSchemaBase` object. |

The role catalog contains supervisor, news translator, news structuring, ontology mapping, macro regime, cycle analysis, equity research, valuation analysis, recommendation review, portfolio risk, paper trading, data quality and operations alert roles. Operational instructions in `AGENTS.md` include accumulated historical execution notes; those notes are not fresh runtime telemetry. Current code/CI and explicit user scope take precedence when reporting progress. PR #34 was in fact merged; the previous chat report stopping at PR #33 was corrected before this task.

## Reproduced defects and fixes

### 1. SDK input could be truncated into invalid JSON

The old builder serialized all fields and then sliced the string to a character limit. This could remove a risk, identifier or closing brace without recording which evidence was omitted. A request-supplied larger limit also bypassed the role's configured budget.

The new renderer keeps valid JSON intact, escapes source-controlled `<`, `>` and `&`, frames it under `source_data`, and measures the complete escaped/framed source section. If it does not fit, it raises `input_budget_exceeded` before provider IO. The effective source limit is the smaller of requested and role-configured limits. This cap does **not** include trusted instructions/schema and is not a token-limit guarantee. Oversized production inputs may now fail rather than silently lose data; real workload shadow validation is still necessary before rollout.

The framing tells the model that raw documents, retrieved summaries, metadata and previous model output are data, not new instructions. It is a defense layer, not proof of resistance to semantic prompt injection. CLI capabilities and runtime OS permissions were not modified.

### 2. SDK output schema was only prompt text

The old Agent had no output schema object and the adapter returned any parsed JSON object. An offline reproduction returned confidence `9` and an undeclared `broker_submit_allowed` field without rejection.

The real SDK Agent now receives a custom `AgentOutputSchemaBase` with the unchanged caller schema. The same schema is checked again after SDK or injected-runner execution. Validation rejects undeclared fields, missing required values, invalid types/enums/ranges, duplicate JSON keys, non-finite numbers and malformed collection shapes. Empty `output`/`result` envelopes cannot fall through to sibling values. Zero remains zero. Error codes do not echo source/model content.

This is intentionally a bounded vocabulary covering the current callers, not a universal JSON Schema engine. Unsupported schema keywords fail before provider IO. No extra schema dependency, role model, fallback selection, dependency pin or financial decision rule was changed. Conforming JSON is not proof that its numbers, claims or citations are true.

### 3. Cycle references accepted a wrong ID if the title looked familiar

The old condition accepted either an allowed ID **or** a known title. A fixture with an unknown ID and a real title was accepted. The new condition requires an integer ID and its exact original/Korean title from the **same** supplied source record. Boolean/string IDs are not silently converted, duplicate supporting references are removed, and filtered references add an uncertainty note.

The Codex cycle caller now validates against the exact bounded source selection sent in the prompt. A reference to an event only present in the full, omitted context is rejected. Existing collection limits remain; the prompt explicitly labels the context as a bounded selection. After the existing list reduction, oversized nested text is rejected rather than sent beyond the cap. The persisted context fingerprint uses the caller's actual budget instead of always using the default budget.

The cycle prompt no longer demands a minimum number of drivers in weak evidence. It separates original source titles from Korean explanations, prior recommendations from independent corroboration, and graph membership/correlation from demonstrated causation. Narrative entailment and causal-path edge correctness are not fully validated by the reference check.

## Version and compatibility

Shared contract version: `2026-09-06-evidence-contract-v1`. Effective runtime policy version/cache metadata appends this contract to the immutable role version. The catalog and its SQL seed remain unchanged. These fields identify the available shared SDK contract; they do not imply that a separately selected Codex builder has been rewritten. Existing news request hashes that use the policy version are conservatively invalidated, including fallback-provider contexts.

Cycle template version: `2026-09-06-cycle-evidence-v3`. Existing `summary_type=cycle_community_ai_v2`, output/storage schema, provider selection and deterministic score rules are preserved. No prompt registration or database update was actually executed here.

## Open findings — not disguised as fixed

1. **Separate Codex news prompts:** the structuring builder still requests Korean `evidence_spans.span_text` while allowing quote/paraphrase, and includes `current_event_impacts` in symbol support. The SDK path is improved, but the separate Codex prompt still needs a bounded migration plus span/source entailment checks. The Codex translator still embeds validation feedback and raw text without the new framing. Existing validators mitigate some outputs, not every semantic issue.
2. **SEC non-finite scalar:** `parse_structured_event_output` uses comparisons that do not reject `NaN` confidence. A deterministic fixture reproduces this parser behavior. This does not claim that an actual database accepted such a record. Address finite numeric and date/identity checks consistently across the SEC path before describing it as hardened.
3. **Equity confidence and evidence pressure:** `_sanitize_valuation_sensitivity` turns explicit confidence `0` into `0.35` through a truthiness fallback. The prompt asks for 3–7 key points even with sparse input; its one-pass bounded selection does not enforce a final character cap. These were inspected/reproduced, not changed by this PR. Targets and scenarios still require source/assumption validation.
4. **Cycle semantics:** exact supporting-event references do not establish that the prose follows those events. Causal paths, numeric confidence defaults and deterministic fallback prose remain separate review targets. Removing invalid references does not automatically regenerate the narrative. Current fallback/reporting behavior was not changed to claim a successful model run.
5. **Provider metadata/settings:** existing model-reported usage and reasoning metadata are not verified SDK telemetry; the existing reasoning-policy field is not proof that an SDK request applied that setting. No provider/model tuning or live behavioral benchmark was performed.
6. **End-to-end quality:** live prompt evaluations, held-out semantic accuracy, original-span entailment, future-information leakage, rejection rates under current workloads, and EC2 rollout remain unverified. Existing golden test data/thresholds and investment weights were not edited to make tests pass.

## Verification method

`verify_analysis_prompt_contract.py` loads 12 deterministic modules and denies actual socket connections and subprocess launches while they run. CI installs the existing `agents` extra and requires that the optional SDK test does not skip. That test constructs a real SDK Agent/schema object but mocks `Runner.run_sync`; it makes no model request. Database executor tests use existing in-memory fakes. One legacy SEC CLI test now mocks the process boundary while retaining its argument/output-file assertions and adding schema/input checks. This is not an operating-system Codex end-to-end test.

The first workflow definition used `runner.temp` at job environment scope, which GitHub does not allow. It was moved to the test step. The next run passed all new contract tests but failed one existing SEC test because its fake Python executable was correctly refused by the no-process guard. The test was isolated as described above; neither the guard nor the contract assertions were weakened. Final exact run/head evidence belongs in the PR and handoff.

No main, actual database access, replacement database, schema/migration, portfolio/order/broker, scoring/weights, benchmark/evaluation split, golden-set changes, account/secrets/AWS, scheduler or production deployment changes. No live paid model call. Frontend files were unchanged; older frontend/browser counts are not presented as newly executed prompt tests.
