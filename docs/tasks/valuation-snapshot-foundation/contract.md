# Task Contract

## Task

- 이름: valuation-snapshot-foundation
- 요청: 전문가식 주식 분석 레이어에 보수적 밸류에이션 스냅샷을 추가한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations valuation-snapshot-run --as-of-date YYYY-MM-DD --execute`가 `market.valuation_snapshot`에 `dcf_lite`, `relative_multiple`, `scenario_range` method를 upsert하고, data-health/cadence/weekly profile에서 추적된다.

## Scope

- 포함:
  - `market.valuation_snapshot` runner
  - SEC companyfacts `shares_outstanding` 적재
  - latest adjusted close 기반 valuation input
  - normalized financial metric과 peer relative context 사용
  - DCF-lite는 positive FCF와 shares outstanding이 있을 때만 생성
  - CLI, cadence, operating-data profile 연결
  - unit/CLI/orchestrator tests
- 제외:
  - recommendation score/weight 변경
  - live broker order submit
  - 유료 valuation data provider
  - frontend valuation 화면 재구성
  - market cap 추정 또는 fabricated target price

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/sec/companyfacts.py`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_sec_companyfacts.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/valuation-snapshot-foundation/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sec_companyfacts tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli valuation-snapshot-run --help`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task valuation-snapshot-foundation`

## Done Criteria

- market cap이 없으면 market cap을 추정하거나 꾸며내지 않는다.
- shares outstanding이 없으면 DCF-lite를 억지로 만들지 않는다.
- 모든 method는 confidence와 assumptions를 저장한다.
- 추천 score/weight는 바뀌지 않는다.
- EC2에서 core filer companyfacts 재수집 후 valuation snapshot execute가 성공한다.

