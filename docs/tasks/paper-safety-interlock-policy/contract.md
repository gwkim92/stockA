# Task Contract

## Task

- 이름: paper-safety-interlock-policy
- 요청: paper validation conflict는 해소됐지만 kill switch/human approval 때문에 validation status가 failed인 상태에서, 추천 weight review와 주문 안전장치를 분리한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-weight-review-readiness-audit-run`이 최신 paper remediation decision이 `paper_actions_waiting_for_safety_interlock_release`이고 paper conflict가 0이면 manual weight review는 허용하되, automatic weight change, automatic order, broker submit은 계속 금지한다.

## Scope

- 포함:
  - 최신 `paper_validation_conflict_remediation` pipeline run decision 조회
  - intentional safety interlock과 paper validation conflict 분리
  - manual weight review gate만 별도로 허용
  - order/broker 관련 gate는 계속 false로 고정
  - unit tests와 EC2 smoke
- 제외:
  - 추천 score/weight 변경
  - paper order 승인
  - kill switch 해제
  - human approval 우회
  - broker live submit
  - UI redesign

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_weight_review_readiness_audit.py`
  - `tests/test_recommendation_weight_review_readiness_audit.py`
  - `docs/tasks/paper-safety-interlock-policy/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py`
  - broker/order submit path
  - kill switch state rows
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_weight_review_readiness_audit tests.test_paper_validation_conflict_remediation`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task paper-safety-interlock-policy`

## Done Criteria

- paper conflict가 있으면 manual weight review는 계속 차단된다.
- paper conflict가 0이고 남은 사유가 intentional safety interlock이면 manual weight review만 허용된다.
- automatic weight change, automatic order, broker submit은 항상 false다.
- 실거래 자동화는 계속 범위 밖이다.
