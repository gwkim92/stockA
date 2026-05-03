# Review

## Review Notes

- 이 작업은 decision-only로 제한했다.
- OpenTelemetry Collector를 app 밖 telemetry egress boundary로 두고, application code는 다음 task에서 optional OTLP exporter pilot만 검증하도록 했다.
- Loki/Prometheus/Alertmanager/Grafana는 reference self-host profile이며 managed backend는 Collector exporter 뒤에서만 교체 가능하게 했다.
- request id, raw path/query, SQL text, DB URL, token, symbol, portfolio, document/thesis/recommendation id는 high-cardinality 또는 secret 위험 때문에 metric/Loki label로 금지했다.
- `/metrics`, OTel dependencies, Collector deployment manifest, alert receiver secret은 추가하지 않았다.
- 별도 AI retrieval docs는 AWH readiness를 통과했지만 이번 task/commit 범위에는 포함하지 않는다.

## Verification Evidence

- `bash scripts/verify_frontend_api_observability_sink_decision.sh`: pass.
- `bash scripts/verify_project_execution_roadmap.sh`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-observability-sink-decision`: pass.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`: pass, 311 tests.
- `git diff --check`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation`: pass for the separate local AI retrieval documents.
