# Task Contract

## Task

- 이름: free-market-backfill-budget-ledger
- 요청: Alpha Vantage 무료 한도를 넘기지 않도록 watchlist queue와 cross-run daily provider budget ledger를 구현한다.
- 담당: Codex
- 날짜: 2026-05-17

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations`가 repo 밖 watchlist와 ledger 파일을 읽어 남은 일일 provider 예산만큼만 `market-price-batch-upsert`를 실행하고, 실제 provider request 수를 cross-run ledger에 누적한다.

## Why

- per-run `--max-requests-per-run`만으로는 하루 여러 번 실행했을 때 무료 quota 초과를 막을 수 없다.
- broad universe backfill 전에 우선순위 watchlist와 daily budget ledger가 필요하다.
- 지금은 schema/API/UI를 동시에 확장하지 않고, 운영 runner 경계에서 quota 보호를 먼저 검증한다.

## Scope

- 포함:
  - repo 밖 CSV watchlist parser
  - repo 밖 JSON daily provider budget ledger
  - `stockanalysis-operations market-price-free-backfill-run` CLI
  - 기존 `run_market_price_batch_upsert` 호출
  - unit tests
  - local no-secret smoke
  - task handoff/review
- 제외:
  - DB schema 변경
  - FastAPI/frontend 화면 변경
  - scheduler actual activation
  - paid provider 도입
  - paper trading/real trading

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/market_price_free_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_market_price_free_backfill.py`
  - `tests/test_data_operations_cli.py`
  - `docs/plans/2026-05-17-free-market-backfill-budget-ledger.md`
  - task docs
- 수정 금지 파일:
  - `db/migrations/`
  - provider API key values
  - broker/order flow
  - host scheduler activation files

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_market_price tests.test_market_backfill -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli market-price-free-backfill-run --watchlist /private/tmp/stockanalysis-runtime/watchlists/free-market-watchlist.csv --ledger /private/tmp/stockanalysis-runtime/alpha-vantage-budget-ledger.json --daily-budget 1 --max-requests-per-run 0 --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-market-backfill-budget-ledger`
  - `bash scripts/verify_project_execution_roadmap.sh`

## Completion Criteria

- [x] operations CLI command exists and refuses repo-inside watchlist/ledger paths.
- [x] ledger tracks used requests per provider/day across runs.
- [x] runner calls ingest batch only with remaining budget.
- [x] tests prove budget exhaustion does not call provider-backed batch upsert.
- [x] no real provider smoke consumes quota unless explicitly configured with positive budget.

## Risks

- Ledger file is local state, so it protects one runtime host only.
- Provider-side quota may already be exhausted even when local ledger says budget remains.
- Free daily prices remain unadjusted; this task does not solve adjusted-price quality.
