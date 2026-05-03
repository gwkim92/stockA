# Review

## Review Notes

- 구현 범위는 optional OTLP exporter pilot에 한정했다.
- `disabled` mode는 기본값이고 OpenTelemetry package를 import하지 않는다.
- `otlp` mode는 `STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT`가 필요하며 endpoint에 userinfo/query/fragment가 있으면 reject한다.
- `/__health`와 startup JSON은 observability mode/runtime metadata만 노출하고 endpoint는 노출하지 않는다.
- access log는 기존 raw path log field를 유지하되 label용으로 쓸 수 있는 bounded `route_template`과 `status_class`를 추가했다.
- `/metrics`, Collector deployment manifest, receiver secret, DB schema, scoring, auth/write/broker flow는 추가하지 않았다.
- unrelated `ai-retrieval-graph-foundation` local docs는 이번 staged/commit 범위에서 제외해야 한다.

## Verification Evidence

- `/tmp/stockanalysis-fastapi-venv/bin/python -m py_compile src/stockanalysis/frontend/observability.py src/stockanalysis/frontend/api_server.py`: pass.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest tests.test_frontend_observability tests.test_frontend_api_server -v`: pass, 23 tests.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_otel_exporter_pilot.sh`: pass.
- `bash scripts/verify_project_execution_roadmap.sh`: pass.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-otel-exporter-pilot`: pass.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests`: pass, 321 tests.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server.sh`: pass.
- `git diff --check`: pass.
