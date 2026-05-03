# Session Handoff

## Active Task

- 이름: frontend-api-otel-exporter-pilot
- 담당: Codex
- 날짜: 2026-05-03

## Current Status

- 완료:
  - task contract와 plan을 만들었다.
  - `src/stockanalysis/frontend/observability.py`를 추가해 `disabled|otlp` mode, OTLP endpoint validation, safe public metadata, route/status helper를 분리했다.
  - API server에 `--observability-mode`, `--otlp-endpoint`, health metadata, startup metadata, bounded access log fields를 연결했다.
  - optional `[project.optional-dependencies].otel` extra를 추가했다.
  - default disabled mode는 OpenTelemetry package 없이 동작한다.
  - `otlp` mode는 endpoint와 optional packages가 없으면 startup boundary에서 실패한다.
  - 다음 고정 task를 `frontend-api-sql-pagination-optimization`으로 이동했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/frontend-api-otel-exporter-pilot/contract.md`
  - `docs/tasks/frontend-api-otel-exporter-pilot/plan.md`
  - `docs/tasks/frontend-api-otel-exporter-pilot/handoff.md`
  - `docs/tasks/frontend-api-otel-exporter-pilot/review.md`
  - `src/stockanalysis/frontend/observability.py`
  - `tests/test_frontend_observability.py`
  - `docs/frontend-api-otel-exporter-pilot.md`
  - `docs/plans/2026-05-03-frontend-api-otel-exporter-pilot.md`
  - `scripts/verify_frontend_api_otel_exporter_pilot.sh`
- 수정:
  - `src/stockanalysis/frontend/api_server.py`
  - `tests/test_frontend_api_server.py`
  - `pyproject.toml`
  - `docs/frontend-api-observability-sink-decision.md`
  - `docs/frontend-api-server.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`

## Decisions

- 기본값은 `STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE=disabled`다.
- `otlp` mode는 endpoint와 optional OTel packages가 있어야 startup에서 활성화된다.
- endpoint는 public health/startup metadata에 노출하지 않는다.
- label/attribute는 low-cardinality route template 중심으로 제한한다.

## Verification Already Run

- `/tmp/stockanalysis-fastapi-venv/bin/python -m py_compile src/stockanalysis/frontend/observability.py src/stockanalysis/frontend/api_server.py` 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest tests.test_frontend_observability tests.test_frontend_api_server -v` 통과, 23 tests.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_otel_exporter_pilot.sh` 통과.
- `bash scripts/verify_project_execution_roadmap.sh` 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-otel-exporter-pilot` 통과.
- `PYTHONPATH=src /tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests` 통과: 321 tests.
- `PYTHON_BIN=/tmp/stockanalysis-fastapi-venv/bin/python bash scripts/verify_frontend_api_server.sh` 통과.
- `git diff --check` 통과.

## Exact Next Step

- exact next step: staged diff에서 secret/high-cardinality regression을 확인한 뒤 commit/push/PR을 만든다.

## Separate AI Retrieval Docs

- 로컬 `ai-retrieval-graph-foundation` 문서는 이번 task 범위 밖이다.
- staging/commit에서 제외한다.

## Risks

- real Collector e2e smoke는 후속 task로 남긴다.
- optional OTel packages는 base venv에 설치하지 않았고, `[otel]` extra로만 선언했다.
- SQL-level pagination optimization은 아직 남아 있다.
- API server smoke는 Docker socket 때문에 기본 sandbox에서 실패했으나, 같은 명령을 승인된 권한으로 재실행해 통과했다.
