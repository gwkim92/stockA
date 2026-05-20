# Session Handoff

## Active Task

- 이름: operating-data-orchestrator
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - Root cause confirmed: market/news/AI ingest had a worker, but the operating-data sequence after ingest was still manual.
  - Task contract and implementation plan created.
  - `stockanalysis.operations.operating_data_orchestrator` added.
  - `stockanalysis-operations operating-data-run` added.
  - The runner defaults to no-write preview and requires `--execute` for DB/provider writes.
  - Repo-outside runtime root, env file, artifact root, generated watchlist CSV, generated position CSV, and output report policy are enforced.
  - Missing event/portfolio symbols are detected before signal generation and backfilled before strategy universe/signal commands run.
  - Portfolio snapshot CSV is generated from source quantities and latest DB prices, not from stale manual fixture prices.
  - Artifact runner now passes loaded env values to child processes without recording those env values in metadata.
  - `/api/data-health` now marks `portfolio-attribution-monthly` as `not_due` when no thesis outcome rows exist, instead of counting it as missing.
  - `/data-health` failure count now uses actionable health statuses (`missing`, `stale`, `failed`) and treats `not_due` as low risk.

## Exact Next Step

- 다음 세션은 이것부터 시작: commit/push 후 EC2에서 코드를 pull하고 `stockanalysis-operations operating-data-run --execute`를 기존 repo-outside runtime env로 1회 실행한다. 그 다음 FastAPI/Next를 재시작하고 `/api/data-health`와 핵심 cockpit routes를 확인한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_artifact_runner tests.test_data_operations_cli tests.test_frontend_live_adapter -v`
- `bash scripts/verify_operating_data_orchestrator.sh`
- `PYTHONPATH=src python3 -m compileall src tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
- `git diff --check`
- Note: default `python3` full unittest is not authoritative on this machine because Python 3.14 has a known `pyexpat` dynamic library failure and lacks FastAPI in that interpreter. The Python 3.13 project venv passed all 662 tests.

## Risks

- 이 runner는 첫 단계에서 scheduler 배포가 아니라 manual/cron 호출 가능한 backend boundary를 만든다.
- 실제 EC2 실행은 repo-outside runtime env가 준비된 상태에서만 가능하다.
- Paper safety/audit is still broker-free and keeps kill switch/broker submission unchanged. It does not make real trading possible.
