# Analysis prompt contract v1 — handoff

## Task and baseline

User request: continue development and inspect prompts. PR #35 on `codex/analysis-prompt-contract-v1`, based on develop@e6ae966d4cdd0aafd03446c3674b4eb6fd62e23f. PR #34 had already been merged and its post-merge Web Product Quality run 33974167198 was successful; the previous chat report stopping at PR #33 was corrected.

The final integration SHA and post-merge verification are recorded on PR #35. Do not treat a checkpoint for an earlier head as verification of a later changed implementation.

## Delivered and reviewed

- Inspected five concrete runtime prompt families (news translation, news structuring, SEC extraction, equity research and cycle summaries), the shared Agents SDK builder, and the 13-role catalog. Role declarations do not mean 13 autonomous agents are deployed. The common SDK executor's current direct consumers are news translation and structuring.
- Added versioned common and task-specific analysis rules distinguishing source data from instructions, facts from hypotheses, raw quotations from translations, units and dates, weak evidence and abstention, and analysis output from trade/score authorization.
- The common SDK source payload is serialized intact and escaped/framed, or rejected before provider IO. No slicing JSON or silently dropping its trailing evidence. Caller input limits cannot expand the configured role limit. The bound covers escaped/framed source characters, not total prompt tokens.
- The existing output schemas now reach an actual Agents SDK AgentOutputSchemaBase object and are validated again before returning. Required fields, extra fields, types, enums, finite numeric values, ranges, collection bounds, duplicate JSON keys and ambiguous empty wrappers are checked without coercing missing/invalid data into success.
- Cycle supporting events require a numeric ID and the exact original/Korean title from the same actually supplied record. Wrong-ID/title-only matches, coerced IDs, duplicates and references only present in omitted context are rejected or filtered with an uncertainty note.
- The cycle prompt allows fewer supported drivers instead of demanding filler claims. Post-selection source size is enforced, and the stored context fingerprint uses the caller's actual context budget. Template version changes without storage/scoring schema changes.

Shared contract: `2026-09-06-evidence-contract-v1`. Cycle template: `2026-09-06-cycle-evidence-v3`; existing summary_type remains `cycle_community_ai_v2`. Registry/seed role versions remain unchanged. Effective runtime metadata appends the shared contract; that is not a claim that separately selected Codex builders were all rewritten.

## Verified implementation checkpoint

Implementation/audit head `42c262cf37316571f36661395929f42bd6e8404a` passed Analysis Prompt Quality run `33979888326`:

- Python 3.11 job `101343108744`: success.
- Python 3.13 job `101343108859`: success.
- Each job ran the same 129 tests from 12 modules, including 26 new prompt-contract cases. Zero failures, errors, skips and unexpected IO attempts in both reports. This is 129 cases checked on two interpreters, not 258 unique tests.
- The already-declared optional SDK resolved to openai-agents 0.17.8. A real Agent/schema object was instantiated, with Runner mocked; generation was not invoked.
- Selected regressions cover the existing registry, news translation/structuring, SEC extraction, equity reporting, cycle summaries/graph context, market context, ontology and unchanged news golden evaluation.
- Socket connects and subprocess launches are denied during tests. Database executor tests use existing in-memory fakes. No real model, database or broker requests occurred.

Downloaded and SHA-256-verified evidence:

- Artifact `9973430887` (Python 3.11), SHA-256 `d7f15c1e7e9e155bc55c1792c489444297624c04a8e16454322c71cfd31a05b5`.
- Artifact `9973430702` (Python 3.13), SHA-256 `4fe74b48469b3e9a093874072b8913a8e9399f7017a7de2997657886097e580f`.

Both JSON reports and logs were inspected, including the 26 new cases. This handoff is the only change after that checkpoint; the resulting head must also pass CI before integration, and PR #35 carries that final result.

## Failures encountered, not hidden

The initial workflow used runner.temp in job-level env, where GitHub does not allow that context. Moving it to the test step fixed workflow validation. The next run executed 129 tests and passed the new SDK/contract tests, but a legacy SEC fixture attempted to spawn a fake Python CLI. The offline guard correctly blocked that process. The test now mocks subprocess.run while retaining CLI arguments and output-file behavior and additionally verifying the schema file and input. The guard and contract thresholds were not disabled. The successful checkpoint has no skipped tests or unexpected IO attempts.

Local targeted tests passed (105 tests with the one optional SDK case skipped). A separate local 129-case guarded run was not fully successful: the source export omitted db migration/seed files needed by three assertions, and the optional SDK was absent. Clean full-checkout CI supplies those files and the SDK. No complete local or full-backend regression success is claimed.

## Remaining limits and next focus

Read `prompt-audit.md` for the full inventory and remaining reproducible findings. Separate Codex news builders retain quote/translation and raw-input framing issues. The SEC parser still has a non-finite-confidence gap. Equity sensitivity still treats explicit zero confidence as a default and has sparse-evidence/minimum-point and final input-cap issues. These paths were inspected and regression-tested but their runtime logic is not changed by this bounded task.

Exact references do not prove that narrative claims follow their evidence, that a causal path is valid, or that a source is truthful. Cycle prose is not automatically regenerated after invalid references are removed. Existing provider usage/reasoning metadata and fallback semantics are not fully remediated. These are next implementation targets, not completed fixes.

Actual current EC2 data, runtime provider selection, live model accuracy, semantic source entailment, future-information leakage, shadow rejection rate, complete backend regression and deployment remain unverified. Oversized source inputs now fail instead of silently losing evidence; assess actual workloads before rollout. No claim of prompt-injection immunity or investment profitability.

No frontend changes or new frontend/browser run was needed for this task; previous UI test counts belong to their earlier commits. No main, dependency/lockfile, database/migration/schema, benchmark/evaluation split or golden-set edits, scoring weight, portfolio/order/broker, account/secrets/AWS, scheduler or production deployment changes. Temporary source export was read-only and removed from the final tree. No independent reviewer approval is claimed.
