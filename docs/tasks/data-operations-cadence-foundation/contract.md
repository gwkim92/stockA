# Task Contract

## Task

- 이름: data-operations-cadence-foundation
- 요청: frontend API runtime/alert boundary 이후 Data Operations Loop의 첫 단계로 daily/weekly/monthly job cadence, artifact boundary, data-health handoff를 repo-local로 고정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 반복 운영 대상 job cadence가 코드와 문서로 고정되고, `/api/data-health` live read가 expected job의 missing/stale/failed 상태를 `ops.pipeline_run` 기준으로 보여줄 수 있다.

## Why

- 장기 투자 운영 시스템은 한 번 실행한 리포트보다 지속적인 freshness와 실패 복구 루프가 중요하다.
- 기존에는 개별 scheduler/remediation smoke가 있으나 전체 데이터 운영 cadence registry와 data-health handoff가 없었다.
- 실제 scheduler 활성화 전 어떤 job이 어느 주기로 돌아야 하는지와 artifact가 어디에 남아야 하는지 먼저 고정해야 한다.

## Scope

- 포함:
  - data operations cadence registry
  - read-only cadence CLI report
  - `/api/data-health` live expected job health 확장
  - artifact root env name and artifact policy documentation
  - docs/task handoff/verification 갱신
- 제외:
  - actual scheduler activation
  - cron/launchd/hosted automation 생성
  - real credentials or production env files
  - DB schema changes
  - write APIs, RBAC, audit write model
  - broker/order flow
  - benchmark/scoring/evaluation split 변경
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/__init__.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `docs/api/frontend/examples/data-health.json`
  - `docs/data-operations-cadence-foundation.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_data_operations_cadence_foundation.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `scripts/verify_frontend_api_alert_rules.sh`
  - `docs/plans/2026-05-03-data-operations-cadence-foundation.md`
  - `docs/tasks/data-operations-cadence-foundation/`
- 수정 금지 파일:
  - `db/migrations/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_data_operations_cadence_foundation.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-cadence-foundation`
  - `git diff --check`

## Deliverables

- Cadence registry and CLI report
- data-health expected job health extension
- Verification script
- Task docs and roadmap updates

## Completion Criteria

- [x] daily/weekly/monthly jobs are represented in code.
- [x] cadence CLI prints JSON without credentials.
- [x] data-health live SQL includes expected job health status.
- [x] artifact root env name is documented without committing a path or secret.
- [x] roadmap moves the fixed immediate next task to generic artifact runner work.
- [x] verification commands pass and evidence is recorded.

## Risks

- This is not production scheduler activation.
- Static cadence thresholds need tuning after real run history exists.
- Actual artifact capture is the next task; this slice only defines the boundary.
