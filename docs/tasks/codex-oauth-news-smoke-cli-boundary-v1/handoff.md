# codex-oauth-news-smoke-cli-boundary-v1 handoff

## Status

- status: in_progress

## Current Status

- 상태: local implementation completed; local verification partially passed; AWH format verification in progress.
- 기준일: 2026-06-20.
- 완료:
  - 뉴스 smoke command boundary를 `sys.executable -m stockanalysis.operations.cli` 기본값으로 변경했다.
  - `STOCKANALYSIS_OPERATIONS_COMMAND` override를 추가했다.
  - 관련 unit test를 추가했다.
- 미완료:
  - EC2 deploy and news smoke rerun are pending.

## Findings

- Codex OAuth direct smoke succeeded and status became `healthy`.
- News smoke failed because FastAPI could not resolve `stockanalysis-operations` from the service PATH.
- EC2 service uses `/opt/stockanalysis/venv/bin/python`; the reliable boundary is module invocation through the active interpreter.

## Changes

- `run_codex_oauth_news_smoke` now builds operations commands from `sys.executable -m stockanalysis.operations.cli` by default.
- Added `STOCKANALYSIS_OPERATIONS_COMMAND` override for deployments that need an explicit command.
- Added regression coverage for the default Python module command.

## Verification

- pending: local and EC2 verification after implementation.

## Exact Next Step

- next: Run local tests, commit/push to `develop`, deploy on EC2, restart FastAPI, and rerun `/__admin/codex-oauth/smoke/news`.

## Next Step

- exact next step: rerun AWH verification, commit and push to `develop`, deploy on EC2, restart `stockanalysis-frontend-api.service`, then rerun `/__admin/codex-oauth/smoke/news`.
