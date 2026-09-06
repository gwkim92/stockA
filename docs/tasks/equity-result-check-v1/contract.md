# Equity result check v1

User requests continued stockA development and a candid assessment of whether it is being built well. Base develop@1981d140bf119045d7fc329736d7deb72126615c. PR #40 is merged; post-merge Analysis Prompt Quality run 34025568582 is successful. Its four retained final-head archives were re-opened in this session and their hashes verified (247 offline cases per Python version, 13 cutoff and 22 committed-write database cases).

## Product outcome

Turn the PR #40 read-only reconciliation function into an actual command in the existing operations CLI. An operator holding run_id/request_hash from an uncertain batch must be able to inspect stored result identity without regeneration, retries, mutation or model calls. Report matching, conflicting, not_observed and unavailable distinctly, with stable exit codes and plain Korean and machine-readable JSON formats. Do not label a current match as analysis accuracy, a missing receipt as rollback, or any state as authorization to retry.

## Scope and acceptance

Validate IDs before any database/config lookup; reuse the existing receipt comparison logic. Restrict database work to a read-only transaction and fixed SELECT, with bounded statement/lock/process timeouts, credential/body-safe diagnostics, no automatic retry and no raw SQL/source/receipt model labels in public output. Integrate with the existing CLI rather than adding a disconnected script. Unit-test actual argument parsing, result formatting, exit codes, wrong identities, malformed responses, timeouts, read-only execution and absence of model/write paths. Exercise the command against the existing disposable PostgreSQL service, including a stored result, overwritten result, missing receipt and database failure; retain all prior prompt/cutoff/atomic tests.

Record a separate candid product quality assessment: implementation reliability, end-user workflow, analysis validity and operational rollout require different evidence. Existing synthetic UI tests and prompt contracts are not live model-quality or investment-value proof. Recommend the next bounded product milestone from actual gaps, not endlessly adding infrastructure tests or claiming world-class readiness.

## Boundaries

No main, production database/EC2 or substitute runtime, schema/migration/seed, dependencies/lockfile, financial weights/thresholds/benchmark/evaluation/golden changes, portfolio/order/broker, accounts/secrets/AWS, scheduler or deployment writes. No paid model call or automatic recovery. Existing bounded synthetic CI database use is allowed. A temporary credential-free read-only tracked-source export may be created and must be removed before integration. Exact final-head and post-merge CI evidence must be recorded; no independent reviewer or full-backend verification claim.
