# Task Contract

## Task

- 이름: manual-weight-review-calibration-report
- 요청: `paper-safety-interlock-policy` 이후 수동 추천 weight 검토가 가능해진 상태를 사람이 읽을 수 있는 calibration report로 고정한다.
- 담당: Codex
- 날짜: 2026-05-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `recommendation-weight-review-calibration-report-run`이 최신 weight review audit eval을 읽고, component별 evidence, 실패/부진 outcome 예시, 안전 경계를 요약한 보고서를 생성한다.

## Scope

- 포함:
  - `ai.eval_run`의 `recommendation_weight_review_readiness_audit` 결과 조회
  - component readiness bucket 요약
  - 최근 non-positive outcome failure case 예시 조회
  - manual review 결론과 next action 생성
  - optional `--execute`에서 `ops.pipeline_run`과 `ai.eval_run`에 보고서 이력 저장
- 제외:
  - 추천 score/weight 변경
  - benchmark/evaluation split 변경
  - paper order 승인
  - kill switch 해제
  - broker live submit
  - 프론트 UI 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/manual_weight_review_calibration_report.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_manual_weight_review_calibration_report.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/manual-weight-review-calibration-report/*`
  - `AGENTS.md`
  - `docs/project-execution-roadmap.md`
- 수정 금지 파일:
  - 추천 weight/scoring formula 적용 경로
  - broker/order submit path
  - kill switch state rows
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_manual_weight_review_calibration_report tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task manual-weight-review-calibration-report`

## Done Criteria

- report는 `manual_weight_review_allowed`, `automatic_weight_change_allowed`, `automatic_order_allowed`, `broker_submit_allowed`를 명시한다.
- 자동 weight 변경은 항상 false다.
- component bucket과 failure case examples가 포함된다.
- EC2에서는 `audit_eval_run_id=16`을 대상으로 smoke가 가능해야 한다.
