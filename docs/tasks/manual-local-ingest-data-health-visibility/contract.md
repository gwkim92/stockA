# Task Contract

## Task

- 이름: manual-local-ingest-data-health-visibility
- 요청: `manual-local-ingest-smoke` 결과를 `/api/data-health`와 `/data-health` 화면에서 안전하게 확인할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: repo-outside summary report가 설정되면 data-health DTO와 화면이 market/news/AI 수동 ingest smoke의 최근 preview/execute 결과를 secret 없이 보여준다.

## Why

- `stockanalysis-operations manual-local-ingest-smoke`는 생겼지만, 현재 결과는 CLI stdout에 머무른다.
- 운영자가 “주식 캔들 수집, 뉴스 수집, AI 분석이 실제로 단발 smoke 됐는지” 화면에서 확인할 수 있어야 한다.
- 반복 자동화가 켜졌는지와 수동 단발 실행이 성공했는지는 다른 개념이므로 UI에서 분리해서 보여줘야 한다.

## Scope

- 포함:
  - `manual-local-ingest-smoke --output` repo-outside summary write
  - `STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT` 기반 sanitized read model
  - `/api/data-health` additive DTO field
  - Next.js `/data-health` operator evidence card
  - tests, verify script, task handoff/review
- 제외:
  - full `--execute` provider/DB run 자동 실행
  - DB schema 변경
  - recommendation scoring/evaluation 변경
  - broker/order flow
  - external server scheduler deployment
  - Mac LaunchAgents/`launchctl` actual mutation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/manual_local_ingest_smoke.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/api/frontend/examples/data-health.json`
  - `docs/frontend-api-contract.md`
  - `tests/test_manual_local_ingest_smoke.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_frontend_live_adapter.py`
  - task docs and verify script
- 수정 금지 파일:
  - repo-inside `.env` secret values
  - DB migrations
  - benchmark/evaluation split
  - broker live order submission
  - host scheduler install paths

## Boundaries

- `--output`은 명시된 repo-outside 경로에만 쓴다.
- API/화면에는 DB URL, API key, bearer token, raw env values를 노출하지 않는다.
- `launchctl bootstrap`, `launchctl kickstart`, `~/Library/LaunchAgents` write/delete는 하지 않는다.
- DTO 변경은 additive로 제한한다.

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_manual_local_ingest_data_health_visibility.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_manual_local_ingest_smoke tests.test_data_operations_cli tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task manual-local-ingest-data-health-visibility`
  - `git diff --check`

## Done Criteria

- [x] CLI can write a secret-free summary to a repo-outside output path.
- [x] Missing/invalid report paths degrade safely in data-health.
- [x] `/api/data-health` includes sanitized `manual_local_ingest_smoke`.
- [x] `/data-health` renders recent manual smoke evidence in Korean.
- [x] Verification evidence is recorded in handoff/review.

## Risks

- Preview evidence proves commands are planned, not that data was written.
- Full `--execute` can consume free provider quota and write DB rows, so it is not run implicitly by this visibility task.
