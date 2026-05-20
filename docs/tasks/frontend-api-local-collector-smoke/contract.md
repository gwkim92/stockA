# Task Contract

## Task

- 이름: frontend-api-local-collector-smoke
- 요청: FastAPI read-only frontend API server의 optional OTLP exporter가 local OTLP receiver로 실제 telemetry를 전송하는 smoke를 추가한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `otlp` mode에서 frontend API server를 local OTLP/HTTP receiver와 함께 실행하면 safe startup metadata를 유지하고, API request 이후 `/v1/traces` POST가 receiver에 도착한다.

## Why

- `frontend-api-otel-exporter-pilot`은 optional dependency/config boundary만 검증했다.
- 실제 exporter가 local telemetry sink로 전송되는지 확인하지 않으면 alert rules나 deployment smoke로 넘어가기 이르다.
- local smoke는 production secret이나 managed vendor 없이 app-to-collector egress boundary를 검증한다.

## Scope

- 포함:
  - local OTLP receiver smoke helper
  - frontend API server `otlp` mode subprocess smoke
  - safe metadata assertion
  - no raw OTLP endpoint exposure assertion
  - verification script
  - docs/task handoff 갱신
- 제외:
  - 실제 OpenTelemetry Collector 배포 매니페스트
  - Loki/Prometheus/Grafana/Alertmanager 배포
  - alert receiver secret
  - public `/metrics` endpoint
  - DB schema/scoring/benchmark/evaluation split 변경
  - auth/RBAC/write endpoint
  - broker/order flow
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `scripts/smoke_frontend_api_local_otlp_receiver.py`
  - `scripts/verify_frontend_api_local_collector_smoke.sh`
  - `tests/test_frontend_observability.py`
  - `docs/frontend-api-local-collector-smoke.md`
  - `docs/frontend-api-otel-exporter-pilot.md`
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-local-collector-smoke.md`
  - `docs/tasks/frontend-api-local-collector-smoke/`
- 수정 금지 파일:
  - `db/migrations/`
  - `apps/web/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile scripts/smoke_frontend_api_local_otlp_receiver.py`
  - `PYTHON_BIN=<python-with-stockanalysis-otel-extra> bash scripts/verify_frontend_api_local_collector_smoke.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_observability tests.test_frontend_api_server -v`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-local-collector-smoke`
  - `git diff --check`

## Deliverables

- Local OTLP receiver smoke helper
- Verification script
- Runtime smoke documentation
- Updated roadmap/handoff/review

## Completion Criteria

- [x] smoke helper starts an OTLP/HTTP local receiver.
- [x] smoke helper starts frontend API server with `observability_mode=otlp`.
- [x] `/__health` reports `instrumented=true` and never exposes the OTLP endpoint.
- [x] at least one `/v1/traces` POST is captured after API reads.
- [x] Verification commands pass and evidence is recorded.

## Risks

- This is an OTLP-compatible local receiver smoke, not full Collector/Loki/Prometheus/Grafana deployment.
- Running the smoke requires a Python environment with `stockanalysis[otel]` optional dependencies installed.
- Metrics export is not asserted in this slice because traces prove the app-to-collector OTLP egress boundary with lower timing flake risk.
