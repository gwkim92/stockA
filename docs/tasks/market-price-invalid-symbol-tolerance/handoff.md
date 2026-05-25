# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `market-price-free-backfill-run --allow-symbol-failures`를 추가했다.
  - 기본 `market-price-free-backfill-run`은 symbol failure가 있으면 non-zero exit를 유지한다.
  - `market-price-daily-run`은 기존 strict failure 동작을 유지한다.
  - `decision-daily`의 `missing-symbol-price-backfill` command에 `--allow-symbol-failures`를 연결했다.
  - CLI/orchestrator regression tests를 추가했다.
  - 변경사항을 커밋/푸시하고 EC2 `/opt/stockanalysis/app`에 fast-forward 배포했다.
  - EC2에서 `decision-daily --as-of-date 2026-05-25 --execute`가 끝까지 성공했다.
  - 최신 추천 `recommendation-141`~`recommendation-146`이 2026-05-25 기준으로 생성됐다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Decisions

- tolerance는 opt-in flag로만 둔다.
- scheduler/main `market-price-daily-run`은 데이터 수집 품질 감시 역할이 있으므로 기본 실패 감지를 유지한다.
- `decision-daily`의 missing-symbol 보강은 보조 단계이므로 실패 symbol을 artifact에 기록하고 계속 진행한다.

## Exact Next Step

- exact next step: `professional-equity-analysis-foundation` 계열의 다음 구현 순서로 넘어간다. 현재 immediate next는 추천 품질/전문가식 분석 고도화이며, 추천 weight 변경은 outcome/eval 근거가 생기기 전까지 금지한다.

## Verification

- 통과:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_market_price_free_backfill_run_allows_symbol_failures_only_when_requested tests.test_data_operations_cli.DataOperationsCliTests.test_market_price_daily_run_keeps_symbol_failures_strict`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_operating_data_orchestrator.OperatingDataOrchestratorTests.test_execute_runs_backfill_before_signal_and_generates_position_csv`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_market_price_free_backfill tests.test_market_price`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task market-price-invalid-symbol-tolerance`
  - EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_market_price_free_backfill tests.test_market_price`
  - EC2: `operating-data-run --profile decision-daily --as-of-date 2026-05-25 --execute --timeout-seconds 600`
  - EC2 route smoke: `/`, `/data-health`, `/recommendations/recommendation-145`, `/stocks/NVDA` returned HTTP 200.
  - EC2 API smoke: `/__health` returned ok and `/api/recommendations/recommendation-145` returned `NVDA`, `2026-05-25`, industry competitive position `advantaged`, peer group `Technology`.
  - EC2 timers: `stockanalysis-operating-data-news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `sec-filings-weekly`, `market-universe-weekly`, `performance-monthly` timers are listed.

## Residual Risk

- `BRK-A` 실패는 artifact에 계속 남아야 한다. 이 작업은 실패를 숨기는 것이 아니라 opportunistic 보강 단계가 전체 의사결정 파이프라인을 막지 않게 하는 것이다.
- `/data-health`는 여전히 품질 감사에서 "오염 의심 항목 확인 필요"를 보여준다. 이는 이번 task 범위가 아니며, 다음 품질/전문가식 분석 고도화에서 계속 다룬다.
