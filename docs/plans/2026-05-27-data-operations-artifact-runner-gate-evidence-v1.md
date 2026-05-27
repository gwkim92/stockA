# data-operations-artifact-runner-gate-evidence-v1

## Summary

- `data_operations_artifact_runner` open gate를 정적 placeholder가 아니라 실제 실행 증거 기반으로 판단한다.
- artifact runner 코드, pipeline run artifact policy, 최신 run evidence, profile scheduler 활성 상태가 있으면 이 gate를 닫는다.
- 개별 job 실패나 degraded 상태는 pipeline run health에서 별도로 다루고, artifact runner 자체 미구현/미사용 문제와 섞지 않는다.

## Scope

- `/api/data-health`에 `data_operations_artifact_runner` payload를 추가한다.
- 기존 SQL 정적 open gate를 Python policy에서 evidence 기반으로 제거하거나 유지한다.
- `/data-health` 자동화 카드와 반복 실행 상세에 artifact runner 증거를 표시한다.
- 테스트는 runner evidence가 없을 때 gate가 열린다는 것과, scheduler/artifact evidence가 있을 때 gate가 닫힌다는 것을 검증한다.

## Non-Goals

- scheduler를 새로 설치하거나 변경하지 않는다.
- pipeline job cadence나 runner command를 변경하지 않는다.
- recommendation score, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- degraded job을 숨기지 않는다. 이 작업은 artifact runner 자체 gate만 정리한다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-operations-artifact-runner-gate-evidence-v1`
