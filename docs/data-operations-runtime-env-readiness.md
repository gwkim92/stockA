# Data Operations Runtime Env Readiness

Date: 2026-05-04

## Decision

`data-operations-runtime-env-readiness` adds the activation gate for recurring data operations runtime env.

This task does not activate a scheduler and does not verify real provider credentials over the network. It checks that a trusted repo-outside env file is ready enough for future scheduler smoke/activation work.

## Interfaces

Render a repo-outside template:

```bash
scripts/render_data_operations_env_template.sh --output /secure/path/data-operations.env
```

Check a trusted repo-outside env file:

```bash
scripts/check_data_operations_runtime_env.sh --env-file /secure/path/data-operations.env
```

CLI boundary:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli \
  data-operations-env-readiness \
  --env-file /secure/path/data-operations.env \
  --repo-root /Users/woody/ai/stockanalysis
```

## Required Env Groups

- `database`: `STOCKANALYSIS_DATABASE_URL` or legacy `STOCKANALYSIS_PSQL_COMMAND`.
- `fred`: `STOCKANALYSIS_FRED_API_KEY`.
- `market_price_provider`: `STOCKANALYSIS_MARKET_PRICE_PROVIDER`, provider key, repo-outside `STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV`, and repo-outside `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH`.
- `sec_identity`: `STOCKANALYSIS_SEC_USER_AGENT` with a descriptive app/contact marker.
- `portfolio_snapshot_source`: `STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV`, absolute existing repo-outside file.
- `openai_or_llm_provider`: `STOCKANALYSIS_LLM_PROVIDER` and provider key env. `openai` requires `OPENAI_API_KEY`.
- `market_price_history`: covered by the configured database boundary; freshness remains a data-health concern.
- `artifact_root`: `STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT`, absolute writable repo-outside directory.

## Security Boundary

- Env template output inside the repository is refused.
- Env checker input inside the repository is refused.
- Portfolio snapshot CSV and artifact root inside the repository are refused.
- Placeholder values such as `CHANGE_ME`, `USER:PASSWORD@HOST`, `/absolute/path`, and `example.com` fail readiness.
- Readiness JSON exposes env variable names and booleans only. It does not expose API keys, DB URLs, user agents, or provider key values.

## Verification

Run:

```bash
bash scripts/verify_data_operations_runtime_env_readiness.sh
```

The verification compiles code, runs targeted unit/CLI tests, checks template rendering, confirms unedited template failure, confirms valid temp env success, checks redaction, checks repo-inside env refusal, and runs the AWH task verification.

## Not Implemented

- Actual scheduler activation.
- Provider network credential smoke.
- Production env file creation.
- Cron, launchd, hosted automations, deployment manifests.
- DB schema changes.
- write APIs, RBAC, audit write model, broker/order flow, benchmark/scoring/evaluation changes.

## Follow-Up Implemented

`data-operations-runtime-smoke` runs representative `macro-weekly` fixture ingest through env readiness and the artifact runner against disposable/local Postgres.

## Next Step

Next fixed task: `data-operations-scheduler-activation-boundary`.

That task should define how the cadence registry is invoked by an actual scheduler without committing host scheduler artifacts or secrets.
