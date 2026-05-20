# Session Handoff

## Active Task

- 이름: manual-local-ingest-smoke
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - preview-first manual local ingest smoke CLI.
  - `stockanalysis-operations manual-local-ingest-smoke` added.
  - Default preview mode does not execute provider/API/DB write commands.
  - `--execute` runs known market/news/AI jobs through the existing artifact runner.
  - Runtime venv Python at `/private/tmp/stockanalysis-runtime/venv/bin/python` is preferred when present.
  - Secret redaction and repo-outside env file requirements are covered by tests.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: `/data-health`가 최신 manual local ingest smoke artifact를 읽도록 visibility boundary를 추가한다.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, external scheduler deployment는 하지 않는다.

## Verification

- `bash scripts/verify_manual_local_ingest_smoke.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task manual-local-ingest-smoke`
- `git diff --check`
- Manual preview: `PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke --job-id market-price-daily --job-id news-rss-daily --job-id event-intelligence-weekly`

## Risks

- 이 작업은 `--execute`가 있을 때 실제 provider/DB write command를 호출할 수 있는 boundary다. 기본 preview mode와 secret redaction을 반드시 유지한다.
- 실제 `--execute` full smoke는 아직 이 task의 verification에서 수행하지 않았다. 다음 단계에서 사용자 의도와 quota를 확인하고 실행 artifact를 `/data-health`에 노출한다.
