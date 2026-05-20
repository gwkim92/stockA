# Task Contract

## Task

- 이름: frontend-api-alert-rules
- 요청: FastAPI read-only frontend API server의 down/not-ready/5xx/timeout/latency/adapter-error alert boundary를 secret 없이 고정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: public repo에 커밋 가능한 Prometheus-compatible alert rule reference와 stdlib validator가 존재하고, receiver secret 없이 frontend API 운영 위험을 감시할 rule boundary가 검증된다.

## Why

- `frontend-api-observability-sink-decision`은 Collector/Prometheus/Alertmanager 방향과 initial alert 후보를 정했다.
- `frontend-api-otel-exporter-pilot`과 `frontend-api-local-collector-smoke`는 optional telemetry egress가 local receiver까지 도달함을 검증했다.
- 다음 단계로 넘어가기 전에 어떤 runtime 상태가 operator alert가 되는지 rule 파일로 고정해야 한다.

## Scope

- 포함:
  - Prometheus-compatible alert rule reference
  - rule validator
  - verification script
  - alert runbook documentation
  - roadmap/README/verification/handoff 갱신
- 제외:
  - Alertmanager receiver routing
  - Slack/email/PagerDuty/OpsGenie/webhook contact config
  - Collector/Prometheus/Grafana deployment manifests
  - public `/metrics` endpoint
  - DB schema/scoring/benchmark/evaluation split 변경
  - auth/RBAC/write endpoint
  - broker/order flow
  - unrelated `ai-retrieval-graph-foundation` local documents

## Mutable Surface

- 수정 가능한 파일:
  - `ops/observability/frontend-api-alert-rules.yml`
  - `scripts/validate_frontend_api_alert_rules.py`
  - `scripts/verify_frontend_api_alert_rules.sh`
  - `docs/frontend-api-alert-rules.md`
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - frontend API verification scripts that assert current immediate next task
  - `docs/plans/2026-05-03-frontend-api-alert-rules.md`
  - `docs/tasks/frontend-api-alert-rules/`
- 수정 금지 파일:
  - `db/migrations/`
  - `apps/web/`
  - production env/secrets/deployment files
  - benchmark/evaluation/scoring files
  - broker/order implementation
  - unrelated `ai-retrieval-graph-foundation` local documents

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_api_alert_rules.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-alert-rules`
  - `git diff --check`

## Deliverables

- Alert rule reference YAML
- Rule validator
- Verification script
- Alert boundary documentation
- Updated roadmap/handoff/review

## Completion Criteria

- [x] six initial alert rules are present.
- [x] receiver/contact destinations are absent from the rule file.
- [x] rule validator rejects high-cardinality or secret-bearing content.
- [x] roadmap moves the fixed immediate next task to Data Operations Loop cadence work.
- [x] verification commands pass and evidence is recorded.

## Risks

- This is a reference rule file, not a running Alertmanager installation.
- Current metric names are the agreed app contract; actual managed telemetry pipeline wiring remains deployment work.
- Alert thresholds are initial operating defaults and should be tuned from production history later.
