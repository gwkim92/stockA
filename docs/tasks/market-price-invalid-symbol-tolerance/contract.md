# Task Contract

## Task

- 이름: market-price-invalid-symbol-tolerance
- 요청: 무료 시장가격 보강 중 일부 provider invalid symbol이 전체 `decision-daily`를 중단시키는 문제를 해소한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `decision-daily`의 opportunistic missing-symbol price backfill은 `BRK-A` 같은 단일 invalid provider symbol을 artifact에 실패로 기록하되 다음 의사결정 단계로 진행할 수 있다. 단, 일반 `market-price-daily-run`의 실패 감지는 그대로 유지한다.

## Scope

- 포함:
  - market price free backfill CLI에 opt-in symbol failure tolerance 추가
  - `decision-daily` missing-symbol-price-backfill command에만 해당 tolerance 적용
  - CLI/orchestrator tests
  - EC2 `decision-daily` rerun smoke
- 제외:
  - provider API key 변경
  - 무료 API 예산 상향
  - watchlist 대규모 재작성
  - recommendation score/weight 변경
  - broker/order submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/market-price-invalid-symbol-tolerance/*`
- 수정 금지 파일:
  - `.env` secret values
  - recommendation scoring weights
  - broker/order submit path
  - DB migrations

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_market_price_free_backfill tests.test_market_price`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task market-price-invalid-symbol-tolerance`

## Done Criteria

- [x] `market-price-free-backfill-run`은 기본적으로 symbol failure가 있으면 기존처럼 non-zero exit를 유지한다.
- [x] `market-price-free-backfill-run --allow-symbol-failures`는 실패 symbol이 있어도 exit 0을 반환하고 JSON에는 실패 count/results를 보존한다.
- [x] `market-price-daily-run`은 기본 실패 감지를 유지한다.
- [x] `decision-daily`의 `missing-symbol-price-backfill` command에는 `--allow-symbol-failures`가 포함된다.
- [x] EC2에서 `decision-daily --as-of-date 2026-05-25 --execute`가 invalid symbol 한 건 때문에 첫 단계에서 멈추지 않는다.
