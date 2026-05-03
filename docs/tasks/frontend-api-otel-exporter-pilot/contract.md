# Task Contract

## Task

- 이름: frontend-api-otel-exporter-pilot
- 요청: FastAPI read-only frontend API server에 optional OTLP exporter pilot boundary를 추가한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 기본 runtime은 OpenTelemetry dependency 없이 `disabled` mode로 그대로 동작하고, `otlp` mode는 safe endpoint/config validation과 optional dependency boundary를 갖는다.

## Why

- `frontend-api-observability-sink-decision`에서 OpenTelemetry Collector를 외부 telemetry egress boundary로 결정했다.
- 다음 단계는 실제 exporter/runtime dependency를 무조건 켜는 것이 아니라, disabled 기본값과 안전한 opt-in 경계를 검증하는 것이다.
- public repo에서 secret, DB URL, request id, raw path/query, symbol, portfolio 같은 고카디널리티 값을 telemetry label로 내보내면 안 된다.

## Scope

- 포함:
  - observability config module
  - `disabled|otlp` mode parsing
  - OTLP endpoint validation
  - optional OpenTelemetry dependency extras
  - FastAPI app health/startup metadata without endpoint leakage
  - bounded route template/status/method attributes for access telemetry
  - unit tests and verification script
  - docs/task handoff 갱신
- 제외:
  - Collector/Loki/Prometheus/Grafana deployment manifests
  - actual alert receiver secrets
  - `/metrics` public endpoint
  - full tracing strategy
  - DB schema/scoring/benchmark/evaluation split 변경
  - write endpoint, RBAC, audit write model
  - broker/order flow
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/observability.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `tests/test_frontend_observability.py`
  - `tests/test_frontend_api_server.py`
  - `pyproject.toml`
  - `docs/frontend-api-otel-exporter-pilot.md`
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/frontend-api-server.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_frontend_api_otel_exporter_pilot.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-otel-exporter-pilot.md`
  - `docs/tasks/frontend-api-otel-exporter-pilot/`
- 수정 금지 파일:
  - `db/migrations/`
  - `apps/web/`
  - env/secret/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/observability.py src/stockanalysis/frontend/api_server.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_observability tests.test_frontend_api_server -v`
  - `bash scripts/verify_frontend_api_otel_exporter_pilot.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-otel-exporter-pilot`
  - `git diff --check`

## Deliverables

- Optional observability config/runtime module
- API server integration
- Tests and verification script
- OTel extra dependency declaration
- Updated docs/task handoff/review

## Completion Criteria

- [x] default disabled mode imports/runs without OpenTelemetry packages installed.
- [x] `otlp` mode requires a safe http/https endpoint.
- [x] endpoint with userinfo/query/fragment is rejected.
- [x] health/startup metadata never exposes OTLP endpoint.
- [x] access log adds bounded route template/status class without raw query.
- [x] next task is moved after this pilot.
- [x] Verification commands pass and evidence is recorded.

## Risks

- `otlp` mode is not runtime-smoked against a real Collector in this slice.
- Optional dependencies are declared but not installed by default.
- OpenTelemetry semantic conventions evolve; the code keeps a conservative low-cardinality boundary.
