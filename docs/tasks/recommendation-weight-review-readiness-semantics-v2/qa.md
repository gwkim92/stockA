# recommendation-weight-review-readiness-semantics-v2 QA

## Status

- local verification completed; live DB execution, push, deployment, and EC2 smoke were not performed.

## Semantic and Security Cases

- all legacy thresholds plus portfolio feedback ready, but integrity policies un-attested: `threshold_evidence_ready=true`, `manual_review_eligible=false`.
- old internally coherent sources: source coherence remains diagnostic, while freshness policy remains un-attested and eligibility stays false.
- missing/invalid quality or feedback counts, impossible count relationships, wrong portfolio, future evidence, source-reference mismatch, nested-quality mismatch: fail closed.
- impossible horizon row partition, recommendation×horizon shape mismatch, missing price fields, aggregate mismatch, and top/nested cohort-filter mismatch: fail closed.
- adversarial authorization/pilot/mutation/order/broker aliases injected into every nested data-health branch: removed by exact projection; all exposed boundaries remain blocked.
- dry-run: four source reads, no write.
- execute test double: only pipeline-run lifecycle and one append-only v2 eval artifact; no domain mutation.

## Passing Evidence

- `bash scripts/verify_recommendation_weight_review_readiness_semantics_v2.sh`: 40/40 passed.
- focused/adjacent Python command from the contract: 251/251 passed.
- `cd apps/web && npm test`: 25 test files / 59 tests passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed; Next.js 16.2.9 production build completed.
- `bash scripts/verify_frontend_api_contract.sh`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- v2 CLI help: passed and exposes no approval/mutation argument.
- `PYTHONPATH=src .venv/bin/python -m compileall -q src tests`: passed.
- `git diff --exit-code -- db/migrations`: passed.
- `git diff --check`: passed.

## Full-Suite Exception

- `PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p 'test_*.py'` ran 1,300 tests and ended with four errors plus one failure.
- all five are outside this task: four `test_data_operations_env_readiness` cases and one ingest-CLI env-readiness assertion now require TossInvest client ID/secret fixtures.
- `src/stockanalysis/operations/env_readiness.py`, `tests/test_data_operations_env_readiness.py`, and `tests/test_ingest_cli.py` have no diff from base `6a397511`; the failures reproduce in an isolated focused command.

## Not Verified

- no live Postgres source selection or v2 append was executed.
- no EC2 runtime, scheduler, FastAPI, or route smoke was run on 2026-07-11.
- no UI rendering changed, so no new visual QA capture was required.
