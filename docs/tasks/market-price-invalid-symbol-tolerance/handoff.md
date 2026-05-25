# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `market-price-free-backfill-run --allow-symbol-failures`를 추가했다.
  - 기본 `market-price-free-backfill-run`은 symbol failure가 있으면 non-zero exit를 유지한다.
  - `market-price-daily-run`은 기존 strict failure 동작을 유지한다.
  - `decision-daily`의 `missing-symbol-price-backfill` command에 `--allow-symbol-failures`를 연결했다.
  - CLI/orchestrator regression tests를 추가했다.
- 진행 중:
  - 로컬 변경을 커밋/푸시한 뒤 EC2에 배포하고 `decision-daily`를 다시 실행해야 한다.
- 막힌 점:
  - 없음.

## Decisions

- tolerance는 opt-in flag로만 둔다.
- scheduler/main `market-price-daily-run`은 데이터 수집 품질 감시 역할이 있으므로 기본 실패 감지를 유지한다.
- `decision-daily`의 missing-symbol 보강은 보조 단계이므로 실패 symbol을 artifact에 기록하고 계속 진행한다.

## Exact Next Step

- exact next step: 변경사항을 커밋/푸시하고 EC2 `/opt/stockanalysis/app`에서 fast-forward pull 후 `decision-daily --as-of-date 2026-05-25 --execute`를 재실행한다.

## Verification

- 통과:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_market_price_free_backfill_run_allows_symbol_failures_only_when_requested tests.test_data_operations_cli.DataOperationsCliTests.test_market_price_daily_run_keeps_symbol_failures_strict`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operating_data_orchestrator.OperatingDataOrchestratorTests.test_execute_runs_backfill_before_signal_and_generates_position_csv`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_market_price_free_backfill tests.test_market_price`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task market-price-invalid-symbol-tolerance`

## Residual Risk

- EC2 `decision-daily`는 아직 재실행 전이다.
- `BRK-A` 실패는 artifact에 계속 남아야 한다. 이 작업은 실패를 숨기는 것이 아니라 opportunistic 보강 단계가 전체 의사결정 파이프라인을 막지 않게 하는 것이다.
