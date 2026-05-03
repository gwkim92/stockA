# Task Contract

## Task

- 이름: frontend-api-observability-sink-decision
- 요청: FastAPI read-only frontend API server의 외부 metrics/log sink와 alerting boundary를 결정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: frontend API server는 어떤 telemetry egress boundary를 채택할지, 어떤 필드/label을 허용할지, 어떤 alert를 먼저 둘지, 다음 구현 task가 무엇인지 문서와 검증으로 고정되어 있다.

## Why

- API server에는 request id, timeout, structured log, probes, deployment boundary, pagination conventions가 있다.
- 하지만 stdout JSON 이후의 외부 sink와 alerting 경계가 정해지지 않아 운영자가 장애를 어디서 감지할지 아직 불명확하다.
- vendor direct SDK나 비공개 secret을 바로 넣으면 public repo와 deployment boundary가 흔들린다.

## Decision

- production egress boundary는 OpenTelemetry Collector를 우선한다.
- application은 당분간 stdout JSON log와 probes를 유지하고, 다음 task에서 optional OTLP exporter pilot을 검증한다.
- backend 후보는 app code가 아니라 Collector exporter 설정으로 교체 가능해야 한다.
- reference self-host profile은 Grafana stack이다: Loki for logs, Prometheus-compatible metrics and alerting, Grafana dashboards.
- alert routing은 Prometheus Alertmanager 계층을 기준으로 문서화하되 Slack/email/on-call receiver secret은 repo에 넣지 않는다.

## Scope

- 포함:
  - observability sink decision 문서
  - telemetry field/label/cardinality policy
  - first alert candidates
  - rejected alternatives와 근거
  - 다음 구현 task slug 결정
  - verification script
  - roadmap/AGENTS/handoff 갱신
- 제외:
  - OpenTelemetry dependency 추가
  - `/metrics` endpoint 추가
  - Collector/Loki/Prometheus/Grafana deployment manifests
  - alert receiver secret 또는 env file 추가
  - DB schema/scoring/benchmark/evaluation split 변경
  - write endpoint, RBAC, audit write model
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/frontend-api-server.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_frontend_api_observability_sink_decision.sh`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-observability-sink-decision.md`
  - `docs/tasks/frontend-api-observability-sink-decision/`
- 수정 금지 파일:
  - `src/stockanalysis/`
  - `apps/web/`
  - `db/migrations/`
  - env/secret/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_api_observability_sink_decision.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-observability-sink-decision`
  - `git diff --check`

## Deliverables

- Observability sink decision doc
- Task contract/plan/handoff/review
- Verification script
- Roadmap/AGENTS next-task update
- Report on whether the separate AI retrieval docs can be continued unchanged

## Completion Criteria

- [x] OpenTelemetry Collector boundary decision is documented.
- [x] Logs/metrics/traces/alerts scope is separated.
- [x] High-cardinality field restrictions are documented.
- [x] Secret/deployment boundaries are explicitly excluded.
- [x] Next implementation task is named.
- [x] Verification commands pass and evidence is recorded.

## Risks

- Decision-only slice does not prove collector runtime behavior.
- Alert thresholds are initial candidates and need tuning with production traffic.
- Vendor-specific backend choice remains deferred to deployment/operator context.
