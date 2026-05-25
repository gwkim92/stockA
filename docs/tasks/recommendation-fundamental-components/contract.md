# Task Contract

## Task

- 이름: recommendation-fundamental-components
- 요청: 추천 row에 재무 품질, 피어 상대 위치, 밸류에이션, 재무 안정성, thesis 일관성 component를 연결한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations recommendation-fundamental-components-run --as-of-date YYYY-MM-DD --execute`가 active recommendation마다 `fundamental_quality_score`, `valuation_margin_score`, `peer_relative_score`, `balance_sheet_risk_penalty`, `thesis_consistency_score`를 `signal.recommendation_score_component`에 weight `0.0000`으로 upsert한다.

## Scope

- 포함:
  - current recommendation batch 기준 active recommendations 조회
  - `market.financial_metric_normalized` 기반 재무 품질 score
  - `market.peer_relative_snapshot` 기반 peer relative score
  - `market.valuation_snapshot` 기반 margin-of-safety score
  - leverage 기반 balance sheet risk score
  - linked thesis 존재/상태 기반 thesis consistency score
  - CLI, cadence, operating-data profile 연결
  - unit/CLI/orchestrator tests
- 제외:
  - recommendation total score 재계산
  - component weight > 0 변경
  - broker/live order submit
  - frontend redesign
  - benchmark/evaluation split 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_fundamental_components.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_recommendation_fundamental_components.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/recommendation-fundamental-components/*`
- 수정 금지 파일:
  - 추천 total score 산식
  - 기존 component weight
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_fundamental_components tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli recommendation-fundamental-components-run --help`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-fundamental-components`

## Done Criteria

- 새 component rows는 idempotent upsert된다.
- 새 component weight는 항상 `0.0000`이다.
- `signal.recommendation.total_score`는 update하지 않는다.
- outcome/eval 표본 없이 추천 weight를 변경하지 않는다.
- EC2에서 execute 후 data-health가 `recommendation_fundamental_components`를 추적한다.

