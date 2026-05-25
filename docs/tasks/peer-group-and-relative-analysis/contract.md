# Task Contract

## Task

- 이름: peer-group-and-relative-analysis
- 요청: 표준화된 재무지표를 사용해 종목별 피어 그룹과 상대 재무 위치를 계산한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations peer-relative-analysis-run --as-of-date YYYY-MM-DD --execute`가 `ref.peer_group`, `ref.peer_group_member`, `market.peer_relative_snapshot`을 갱신하고, data-health/cadence/weekly profile에서 추적된다.

## Scope

- 포함:
  - normalized financial metrics 기반 peer group coverage runner
  - classification membership 기반 peer group 생성
  - fallback coverage group 생성
  - metric별 peer median, percentile rank, relative signal 계산
  - CLI, cadence, operating-data profile 연결
  - unit/CLI/orchestrator tests
- 제외:
  - recommendation score/weight 변경
  - valuation snapshot 산출
  - Codex OAuth 리서치 리포트 생성
  - frontend redesign
  - broker live order submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/peer-group-and-relative-analysis/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task peer-group-and-relative-analysis`

## Done Criteria

- 피어 비교는 `market.financial_metric_normalized`의 computed metric만 percentile 계산에 사용한다.
- 분류 기반 피어 그룹이 부족해도 fallback coverage group으로 최소 비교 경로가 생긴다.
- peer group member와 relative snapshot upsert는 idempotent하다.
- 추천 weight는 바뀌지 않는다.
