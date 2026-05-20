# Task Contract

## Task

- 이름: local-ingest-worker-loop
- 요청: 수동으로 검증된 market/news/AI local ingest smoke를 안전한 로컬 process worker로 반복 실행 가능하게 한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations local-ingest-worker-run` 명령이 기본 preview 1회로 안전하게 동작하고, 명시적 `--execute --max-cycles N`일 때만 market/news/AI jobs를 반복 실행하며, 최신 smoke summary를 repo 밖 파일로 갱신할 수 있다.

## Why

- 수동 `manual-local-ingest-smoke --execute`는 실제 Postgres/FastAPI/Next 경로에서 검증됐다.
- 하지만 아직 반복 실행 단위가 없다. Mac LaunchAgents나 외부 scheduler부터 켜면 운영 경계가 다시 흔들린다.
- 먼저 Python operations backend 안에 bounded local worker를 만들어야 이후 server scheduler나 배포 scheduler가 같은 service boundary를 호출할 수 있다.

## Scope

- 포함:
  - local ingest worker service
  - operations CLI command
  - repo-outside latest smoke summary update
  - focused tests and verify script
  - roadmap/handoff/review docs
- 제외:
  - Mac LaunchAgents/`launchctl` actual mutation
  - external server scheduler deployment
  - DB schema 변경
  - recommendation scoring/evaluation 변경
  - paid LLM/OpenAI call 도입
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/local_ingest_worker.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_local_ingest_worker.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_local_ingest_worker_loop.sh`
  - task docs, roadmap docs
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring
  - benchmark/evaluation split
  - host scheduler install files

## Boundaries

- 기본 실행은 provider/API/DB write를 하지 않는 preview다.
- 실제 write는 `--execute`가 있을 때만 허용한다.
- `max_cycles`는 양수 bounded 값이어야 한다.
- `smoke-output`과 `output`은 repo 밖 경로만 허용한다.
- 실제 `launchctl`이나 LaunchAgents write/delete는 하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_local_ingest_worker tests.test_data_operations_cli`
  - `bash scripts/verify_local_ingest_worker_loop.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-ingest-worker-loop`
  - `git diff --check`

## Done Criteria

- [x] Worker preview mode does not call provider/API/DB write jobs.
- [x] Worker execute mode delegates bounded cycles to `manual-local-ingest-smoke`.
- [x] Worker can update a repo-outside latest smoke summary file for `/data-health`.
- [x] CLI exposes the worker through `stockanalysis-operations`.
- [x] Verification evidence is recorded.
