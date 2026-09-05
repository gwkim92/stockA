# Analysis prompt hardening v2

User: continue carefully; inspect and improve the project to a very high quality standard. Continue the identified runtime prompt defects rather than starting another unrelated screen. Base develop@04c6c3799625f2d808e256ca219b097ddc990f34 (PR #35).

## Outcome

Correct reproducible SEC and equity numeric-validation errors and close the inconsistent source/instruction and quotation rules in separate Codex news prompt paths. Check actual builders, input serialization, provider calls, output parsers, validation gates and failure handling. Quality claims require regression evidence; this task cannot establish world-leading investment performance from deterministic tests.

## Planned boundaries and acceptance

- SEC: finite typed confidence/significance, validated thresholds and dated event output; prevent invalid parsed or provider-runner values from reaching canonical candidate construction. Preserve existing candidate thresholds and event taxonomy.
- Equity: preserve explicit zero; reject non-finite, wrong-type and out-of-range model confidence rather than clamping; bound the actual prompt source selection; remove minimum-output pressure on sparse evidence. Keep missing values explicit and compatible with the existing declared output schema.
- Codex news translation/structuring: use the common untrusted-source framing; exact original-language spans versus Korean explanations; surrounding retrieved context must not masquerade as direct source evidence. Preserve public entrypoints, model/provider choices, CLI permissions and existing golden-set criteria.
- Add adversarial tests before fixes; verify baseline defects, happy paths, truncation/budget edge cases and integration gates with fake executors. Expand the existing offline Python 3.11/3.13 CI, do not relax expected results or use paid/live calls.
- Inspect final diff, record scoped findings and remaining semantic risks, and merge only the tested final head into develop. Real workloads, model accuracy and rollout remain unverified.

No main, database queries/mutations or replacement DB, migrations/storage schema, golden set/benchmark/evaluation split, scoring weights, portfolio/order/broker, dependencies/lockfiles, secrets/accounts/AWS, scheduler or deployment configuration changes. No live model call. A temporary read-only source/test archive may be used because this sandbox has no GitHub DNS; only tracked source, tests, existing DB test fixtures and docs are exported, no .git credentials or runtime files. Remove that helper before integration.
