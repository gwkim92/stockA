# Task Contract

## Task

- 이름: recommendation-weight-review-readiness-audit
- 요청: `ready_for_weight_review`가 나온 추천 품질 평가 결과를 다시 감사해, 실제 추천 weight 검토를 열어도 되는지 판단한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations recommendation-weight-review-readiness-audit-run --as-of-date YYYY-MM-DD`가 최신 또는 지정된 `recommendation_quality_calibration` eval 결과를 읽고, sample/professional coverage/zero-weight guardrail/paper validation을 종합해 `ready_for_manual_weight_review` 또는 차단 사유를 반환한다.

## Scope

- 포함:
  - `ai.eval_run`의 recommendation quality eval 결과 조회
  - paper validation conflict, missing validation, insufficient sample, insufficient professional coverage, unapproved weight mutation 차단
  - component별 spread를 review-only candidate로 정리
  - `--execute` 시 감사 결과를 `ai.eval_run`과 `ops.pipeline_run`에 저장
  - CLI와 unit/CLI tests
- 제외:
  - 추천 점수 산식/weight 변경
  - 추천 row 재생성
  - paper order 생성/제출
  - broker live submit
  - frontend redesign
  - Codex OAuth 호출

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_weight_review_readiness_audit.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_recommendation_weight_review_readiness_audit.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/recommendation-weight-review-readiness-audit/*`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
- 수정 금지 파일:
  - `src/stockanalysis/signal/recommendation.py` scoring weights
  - DB scoring migrations
  - benchmark/evaluation split
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_weight_review_readiness_audit tests.test_data_operations_cli`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-weight-review-readiness-audit`

## Done Criteria

- audit runner는 추천 weight를 절대 변경하지 않는다.
- `ready_for_weight_review`라도 paper validation이 `failed`이거나 conflict가 있으면 차단한다.
- 통과 조건은 manual review 열기까지만 허용하며, automatic weight change는 항상 `false`다.
- component별 후보는 review-only이며 별도 pilot-weight task 전까지 총점에 반영하지 않는다.
