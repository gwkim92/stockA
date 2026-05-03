# Session Handoff

## Active Task

- 이름: frontend-api-observability-sink-decision
- 담당: Codex
- 날짜: 2026-05-03

## Current Status

- 완료:
  - task contract와 plan을 만들었다.
  - `docs/frontend-api-observability-sink-decision.md`에서 OpenTelemetry Collector를 production telemetry egress boundary로 고정했다.
  - reference self-host stack을 Loki, Prometheus-compatible metrics, Alertmanager, Grafana로 정리했다.
  - request id, raw query string, SQL text, DB URL, token, symbol, portfolio, document/thesis/recommendation id를 metric/Loki label로 금지했다.
  - 첫 alert 후보를 정의하되 receiver secret/deployment config는 repo 밖 boundary로 남겼다.
  - 다음 고정 task를 `frontend-api-otel-exporter-pilot`으로 이동했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-api-observability-sink-decision/contract.md`
  - `docs/tasks/frontend-api-observability-sink-decision/plan.md`
  - `docs/tasks/frontend-api-observability-sink-decision/handoff.md`
  - `docs/tasks/frontend-api-observability-sink-decision/review.md`
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/plans/2026-05-03-frontend-api-observability-sink-decision.md`
  - `scripts/verify_frontend_api_observability_sink_decision.sh`
- 수정:
  - `docs/frontend-api-server.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Decisions

- OpenTelemetry Collector를 production telemetry egress boundary로 채택하는 방향이다.
- app은 vendor direct sink가 아니라 optional OTLP exporter pilot을 다음 task에서 검증한다.
- stdout JSON/probes는 유지한다.
- external deployment/secret/receiver 설정은 repo 밖 boundary로 남긴다.

## Verification Already Run

- `bash scripts/verify_frontend_api_observability_sink_decision.sh` 통과.
- `bash scripts/verify_project_execution_roadmap.sh` 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-observability-sink-decision` 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests` 통과: 311 tests.
- `git diff --check` 통과.

## Exact Next Step

- exact next step: `frontend-api-otel-exporter-pilot` task contract를 만들고, default disabled optional OTLP exporter pilot을 검증한다.

## Separate AI Retrieval Docs

- 로컬에 `ai-retrieval-graph-foundation` 문서가 남아 있다.
- 이번 task의 staged/commit 범위에는 포함하지 않는다.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation`는 통과했다.
- 다른 세션은 그대로 참고해도 되지만, 바로 코드 구현을 시작하지 말고 `ai-retrieval-adapter-foundation` 같은 별도 task contract를 먼저 만들어야 한다.
- 그 세션은 `frontend-api-otel-exporter-pilot` current immediate task와 파일 소유권이 충돌하지 않는지 `git status --short`로 확인해야 한다.
- standalone plan에는 code implementation step이 있으므로, 문서-only foundation task와 실제 code task를 혼동하지 않아야 한다.

## Risks

- 이번 slice는 decision-only라 실제 collector/exporter runtime은 검증하지 않는다.
- 첫 alert threshold는 production traffic이 생기면 조정해야 한다.
- 외부 receiver secret과 deployment manifest는 의도적으로 repo에 없다.
