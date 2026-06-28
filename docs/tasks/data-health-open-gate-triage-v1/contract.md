# data-health-open-gate-triage-v1 Contract

## Task Request

- request: `/api/data-health`와 `/data-health`에서 open gate가 실제 장애, 실행 기한 도래, 관리된 대기, 투자 검토, 원천 한계로 정확히 분류되도록 수정한다.
- context: EC2의 현재 `/api/data-health`는 alert stale, artifact 실패, AI quota 실패 같은 실제 조치 항목과 outcome due/wait/source-limit 항목을 모두 open gate로 노출해 사용자가 무엇을 지금 처리해야 하는지 구분하기 어렵다.

## Goal

- goal: `/api/data-health`와 `/data-health`에서 사용자가 지금 복구할 장애, 지금 실행할 성과 작업, 기다릴 성과 표본, 투자 검토, 원천 한계를 한눈에 구분할 수 있다.

## Scope

- `src/stockanalysis/frontend/live_adapter.py`의 open gate policy와 detail mapping을 정리한다.
- 필요한 경우 `/data-health` presentation copy만 보정한다.
- unit test로 managed wait/source-limited 항목이 불필요한 open gate가 되지 않는지, actionable due 상태가 명확한 category/detail을 갖는지 고정한다.
- `docs/tasks/data-health-open-gate-triage-v1/handoff.md`를 갱신한다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/data-health/_components/dataHealthGateModel.ts`
  - `apps/web/src/app/data-health/_components/dataHealthGateModel.test.ts`
  - `docs/tasks/data-health-open-gate-triage-v1/*`

## Non Goals

- 추천 weight 변경 금지.
- DB schema 변경 금지.
- scheduler/systemd 설정 변경 금지.
- 실거래 broker submit 구현 금지.
- alert, AI quota, data runner 장애를 숨기지 않는다.

## Acceptance Criteria

- `alert_destination`, `data_operations_artifact_runner`, `live_ai_invocation_health_attention`처럼 실제 운영 조치가 필요한 항목은 계속 열린 항목으로 남는다.
- 성과 성숙 대기, 이미 관리 중인 포트폴리오 검토, durable source blocker는 장애처럼 보이지 않는다.
- due action이 필요한 recommendation outcome 또는 portfolio feedback은 `outcome_due` 성격의 명확한 detail을 갖는다.
- `/data-health`에서 raw snake_case와 일반적인 “조건 미충족” 문구가 핵심 카드에 새로 늘지 않는다.
- 하네스 task handoff가 다음 사람이 이어받을 수 있게 남는다.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-open-gate-triage-v1`

## Risk Notes

- 현재 EC2는 OpenAI quota 부족과 artifact runner 실패가 실제 운영 조치로 남아 있다. 이 task는 그 장애를 해결하지 않고 정확히 분류한다.
- open gate 수가 줄어도 “문제 없음”을 의미하지 않을 수 있다. managed wait/source limit은 별도 카드로 계속 보여야 한다.
