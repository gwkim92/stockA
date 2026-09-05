# Verification record

## Local allowed-change checkpoint

The isolated working copy contains only the successfully uploaded SEC and news changes. The blocked equity patch and its modified expectations are excluded.

`python scripts/verify_analysis_prompt_contract.py` ran 159 selected cases from 14 modules: zero failures, zero errors, zero unexpected IO attempts, one skipped optional-SDK test because openai-agents is not installed in the local sandbox. The existing CI installs the declared agents extra and uses --require-sdk, which rejects skips. These are not results from a live model, database or OS Codex process.

New cases: 14 SEC tests and 16 news/translation tests, including multiple adversarial subcases. The remaining 129 cases are the existing selected regressions. Do not count subcases or two Python interpreters as additional unique test methods.

Test coverage includes:

- SEC finite/type/range checks, default threshold preservation, measured zero, empty-string round trips, required/extra fields, timestamps, invalid budget before IO and mismatched chunk before Codex.
- Typed SEC provider bypass attempts result in a failed pipeline, with no canonical event INSERT in the fake executor log.
- Framed original metadata, role-like text, context and validation errors; actual Codex schema file/CLI argument inspection with subprocess mocked.
- Literal original spans accepted; invented, metadata-only and translated spans rejected. The same check is exercised through SDK, Codex and injected-provider paths.
- Invalid news output cannot insert extraction/impact records; invalid typed translation output cannot update a source document. A valid literal quote still completes the existing accepted path.
- Metadata-only company names do not bypass the existing direct-company gate in the actual runner.
- The unchanged golden news evaluator and existing registry, cycle, equity, market-context and ontology tests remain in the selected suite.

## Review checks

The local runtime blobs were compared to the GitHub versions after upload: SEC 5911f0072c46e24fecd852aa14df45da7335033e; translation 1080543b2d7e095145cd55289dcffd2b1dab418f; news structuring b55cb51da5f7e2fd83843c3f669b4119f290e9ba. A function-level AST comparison confirms SQL builder bodies in these files are unchanged. The equity file and its tests are unchanged from baseline. Syntax compilation and diff whitespace checks passed.

The initial focused negative-test experiment reproduced SEC NaN/boolean/numeric-string acceptance and the separately blocked equity defaults; its broad experimental results are not used as proof that the unuploaded equity fixes reached this branch. SEC infinity was already rejected by the old range comparison; the new validation rejects it consistently but does not claim that particular case was previously accepted.

## Required integration evidence

The final PR must record the exact final head, Python 3.11/3.13 CI runs, inspected JSON/log artifacts and post-merge result. A green local subset does not authorize claiming full-backend, live model or browser verification. Existing socket/subprocess guards stay enabled; no golden data, thresholds or assertions are relaxed to obtain a pass.
