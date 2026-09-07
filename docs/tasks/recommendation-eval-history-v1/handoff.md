# Recommendation evaluation history: backend handoff

Date: 2026-09-07
Repository: gwkim92/stockA
PR: #49, targeting develop
Base: 1d9d8dcc3699152a1fe435a304d95d96d930b9b1 (merged persistence PR #48)
Verified implementation and CI-fix head: ad366a6aa8baeeb39c626a63610044f294d7da3f
Verified PR merge ref: 9fa2f8a27666da825e7497c4101c86f383a5f784

## Delivered slice

The read-only history foundation is implemented. The original contract describes a broader history-reader/UI objective; UI presentation, hash re-verification and historical comparison are NOT completed by this backend slice.

- GET `/api/recommendation-evaluations?limit=25&before=<eval ID>` lists only `recommendation_quality_calibration` runs, descending numeric eval ID.
- GET `/api/recommendation-evaluations/eval-run-<ID>?limit=25&after=<snapshot ID>` reads the exact run and its saved snapshots, ascending numeric snapshot ID.
- The dedicated top-level DTO is `recommendation-eval-history-v1`. It is not wrapped in an existing frontend dashboard DTO, and there is no frontend UI consumer yet.
- Default page size is 25, maximum 100. Keyset pagination uses one sentinel row and the last visible ID as cursor. `pagination.scope=returned_page_only` must not be treated as a whole-history performance aggregate.
- Canonical positive bigint selectors only. Duplicate, unknown, malformed and out-of-range selectors fail before runtime configuration or SQL access. Raw controls are rejected before URL normalization.
- The existing API adapter dispatches these routes before mutable live/fixture resolution. Existing bearer authentication, no-store headers, timeout and write-method denial remain in place.

## Historical data semantics

The reader queries only `ai.eval_run` and `ai.recommendation_eval_snapshot`, after a schema-readiness check. It does not reconstruct history from mutable recommendation, thesis, instrument or outcome tables and never backfills source state.

Runs distinguish `legacy_unavailable`, `recorded_empty`, `count_mismatch` and `recorded`. Missing schema/connectivity is an unavailable source, not a successful empty result. Missing or wrong-family exact run IDs are not replaced by the latest run. Error codes retain the existing HTTP 400/404/503 mapping.

Top-level run, snapshot and source IDs are strings. `snapshot_json` is returned as saved parsed JSON, without rewriting nested numeric fields; future JavaScript consumers must use the string identity fields rather than coercing raw nested IDs to Number.

`history_basis=evaluation_time_snapshot_not_recommendation_creation_time` is explicit. These records are evaluation-time captures, not proof of knowledge at the original recommendation creation time and not current market state.

The saved `snapshot_sha256` is exposed but NOT recomputed. `snapshot_hash_verification=not_performed` prevents an integrity or authenticity claim. A future verifier must first test the persistence canonicalizer through a real JSONB round-trip, including decimals, exponent notation, Unicode and large IDs. It must distinguish unsupported schema, invalid payload, hash mismatch and unavailable verification without repairing stored records.

## Executed verification

Both workflows completed successfully for ad366a6aa8baeeb39c626a63610044f294d7da3f:

- Evaluation History: https://github.com/gwkim92/stockA/actions/runs/34097907034
- Evaluation History Read Contract: https://github.com/gwkim92/stockA/actions/runs/34097907053

Their test sources were unchanged by the two CI-only fixes. Detailed test-count evidence was also inspected in the preceding implementation runs 34097418721 and 34097418643:

| Suite | Passed test methods |
| --- | ---: |
| Existing analysis integrity regression | 93 |
| Existing operations CLI regression | 107 |
| History unit and HTTP tests | 19 |
| Existing frontend API server regression | 18 |
| History integration through the real PsycopgPoolExecutor | 9 |
| Supplemental history reader/HTTP contract | 27 |
| Supplemental SELECT-only PostgreSQL integration | 8 |

The Evaluation History workflow reports the 19 + 18 + 9 = 46 combined tests with zero failures, zero errors and zero skips, and retains `evaluation-history-results/result.json` as a workflow artifact. The shared 93 + 107 regression tests execute in both workflows; repeated execution is not additional unique coverage. There are overlapping scenarios between the two history suites.

The real-pool integration applied all 35 checked-in migrations to a fixed loopback disposable database. It verified keyset paging, exact family/run isolation, bigint boundaries, zero versus null, missing children/schema, restricted reader permissions, pool recovery after rejected writes, and unchanged saved history after actual synthetic source recommendation UPDATE and DELETE.

The previous supplemental workflow failure was solely `HEAD^` missing in a depth-one checkout, after all functional steps passed. Both workflows now fetch depth two and run `git diff --check HEAD^ HEAD`, checking committed changes rather than an empty worktree diff. The formerly failing diff step was observed successful in run 34097907053.

Execution environment observed in the detailed logs: Python 3.11.16, psycopg 3.3.5, PostgreSQL 16.15. Dependency deprecation warnings exist; no unrelated package upgrades were made.

## Boundaries and unverified items

No new or modified schema/migration/seed files, scoring logic, weights, benchmarks, policy thresholds, order/broker paths, secrets, scheduler, AWS, main or deployment configuration. Existing migrations and synthetic writes ran only inside disposable CI service databases. No production database or paid/live model invocation was used.

Local container/Python execution was unavailable in this session; no local pass is claimed. CI evidence is for the backend slice, not a full repository test run, a frontend build/browser validation, production load validation or deployment. No end-user history screen, hash verification, current-versus-historical drift comparison, later-outcome comparison or migration backfill is delivered here.

## Next implementation boundary

Build a typed server-side UI adapter for this dedicated DTO and a run/snapshot reader using explicit string IDs, bounded paging and the four storage states. Label evaluation-time capture, unverified hashes and page-only scope. Add frontend tests and browser checks before claiming the history screen is complete. Keep any current-state comparison visibly separate from saved evaluation content and make no order/weight permission changes.
