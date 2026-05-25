# Task Contract

## Task

- 이름: recommendation-quality-professional-coverage-guardrail
- 요청: 추천 weight 검토 전에 전문가식 분석 레이어 coverage를 `recommendation-quality-eval-run`이 확인하게 만든다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-quality-eval-run` 결과가 active recommendation별 재무지표, 피어 비교, 밸류에이션, 산업 경쟁 위치, 기업 리서치 artifact, active thesis coverage를 집계하고, coverage가 기준 미만이면 `ready_for_weight_review`가 되지 않는다.

## Scope

- 포함:
  - recommendation quality eval SQL에 professional analysis coverage 집계 추가
  - scoring guardrail에 minimum professional coverage rate 추가
  - CLI flag `--min-professional-coverage-rate`
  - unit/CLI tests
  - task handoff
- 제외:
  - 추천 score formula/weight 변경
  - DB schema/migration
  - 신규 리서치 artifact 생성
  - broker/order submit
  - repo 안 secret/env 값

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_quality_eval.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_recommendation_quality_eval.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/recommendation-quality-professional-coverage-guardrail/*`
- 수정 금지 파일:
  - recommendation score formula/weights
  - benchmark/evaluation split
  - DB migrations
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-quality-professional-coverage-guardrail`

## Done Criteria

- eval SQL은 professional coverage layer count와 gap examples를 반환한다.
- coverage가 기준 미만이면 outcome sample이 충분해도 `quality_status`는 `needs_more_data`다.
- coverage가 충분하고 protected component weight가 모두 0이며 sample이 충분할 때만 `ready_for_weight_review`가 가능하다.
- 추천 weight는 변경하지 않는다.
