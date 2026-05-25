# Task Contract

## Task

- 이름: recommendation-quality-fundamental-guardrail
- 요청: 추천 품질 평가가 재무·밸류에이션·피어·thesis component weight 변경 여부를 명시적으로 차단/보고하게 만든다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-quality-eval-run` 결과에 `fundamental_quality_score`, `valuation_margin_score`, `peer_relative_score`, `balance_sheet_risk_penalty`, `thesis_consistency_score`의 zero-weight guardrail이 포함되고, 하나라도 weight가 0이 아니면 `ready_for_weight_review`가 되지 않는다.

## Scope

- 포함:
  - recommendation quality eval SQL에 protected fundamental component guardrail 추가
  - score payload에 `fundamental_weight_guardrail` 추가
  - next action 문구에 재무/밸류에이션 weight 변경 차단 사유 추가
  - unit tests 갱신
  - task handoff 갱신
- 제외:
  - 추천 score formula/weight 변경
  - outcome 산식 변경
  - paper order 생성
  - frontend redesign
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_quality_eval.py`
  - `tests/test_recommendation_quality_eval.py`
  - `docs/tasks/recommendation-quality-fundamental-guardrail/*`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - DB migrations
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_quality_eval`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-quality-fundamental-guardrail`

## Done Criteria

- [x] SQL lookup이 protected fundamental component들을 guardrail 대상으로 집계한다.
- [x] score payload가 `fundamental_weight_unchanged`를 반환한다.
- [x] protected fundamental component weight가 0이 아니면 quality status가 `needs_more_data`로 남는다.
- [x] 추천 산식과 DB schema는 변경하지 않는다.
