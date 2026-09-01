# recommendation-weight-review-source-lineage-reconciliation-v1 QA

## Result

- focused verification: passed
- focused unit tests: 14 passed
- Python compile: passed
- CLI help and safety scan: passed
- package entry-point parse: passed
- remote blob integrity check: passed for core module, CLI, tests, verifier, operator documentation, and `pyproject.toml`

## Commands Executed

```bash
bash scripts/verify_recommendation_weight_review_source_lineage_reconciliation_v1.sh
```

The verifier performs:

- `compileall` for the core module, CLI, and focused test module;
- focused `unittest` execution;
- CLI `--help` smoke;
- required flag checks;
- unsafe approval/pilot/weight/order/broker flag rejection;
- atomic lookup read-only SQL assertions;
- append-only eval insert assertions;
- `git diff --check` when a full worktree is available;
- migration-change rejection when a local `develop` ref is available.

Focused test result:

```text
Ran 14 tests
OK
recommendation weight review source lineage reconciliation v1 verification passed
```

Package metadata check:

```bash
python3 - <<'PY'
import tomllib
with open('pyproject.toml', 'rb') as handle:
    project = tomllib.load(handle)
assert project['project']['scripts']['stockanalysis-weight-lineage-reconciliation'] == (
    'stockanalysis.operations.'
    'recommendation_weight_review_source_lineage_reconciliation_cli:main_entry'
)
PY
```

## Acceptance Coverage

- exact readiness-referenced quality/outcome selection: covered
- independent latest drift remains diagnostic: covered
- canonical-chain hash stability under latest drift: covered
- canonical-chain hash change under referenced evidence change: covered
- missing source/reference fail closed: covered
- wrong source identity/reference/status fail closed: covered
- future-dated source fail closed: covered
- required cohort filter identity and mismatch: covered
- nested quality canonical hash equality: covered
- adversarial permission escalation: covered
- one-read dry-run with no writes: covered
- execute writes only pipeline lifecycle and one append-only eval: covered

## Not Executed In This Environment

- live PostgreSQL lookup against production/development `ai.eval_run` history
- Docker-backed full repository verification
- complete repository unit/integration regression suite
- OS scheduler, deployment, broker, or order smoke

The runtime cannot resolve `github.com`, so a complete repository clone was unavailable. To avoid claiming broader evidence than exists, QA was run against the exact branch file contents after Git blob SHA comparison and against locally reconstructed existing helper interfaces. No live data, schema, score, position, order, or deployment mutation was performed.
