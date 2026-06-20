# codex-oauth-admin-action-async-v1 Handoff

## Status

- status: completed
- current status: implemented, pushed to `develop`, deployed to EC2, and smoke verified.
- completed: Codex OAuth news smoke now runs as a background admin action, EC2 open gates are clear, and service route smoke passed.

## Current Status

- status: implemented, pushed to `develop`, deployed to EC2, and smoke verified.
- 상태: completed.
- 기준일: 2026-06-20.
- 발견한 장애:
  - OAuth 자체는 정상이다.
  - 이전 `뉴스 AI 확인` 실패 1차 원인은 FastAPI systemd PATH가 `stockanalysis-operations`를 못 찾는 문제였다. 이 문제는 이전 task에서 `sys.executable -m stockanalysis.operations.cli`로 해결했다.
  - 이후 실패 2차 원인은 FastAPI `NoNewPrivileges=true`와 data operations env의 `sudo docker exec` 충돌이었다. EC2 runtime env에서 `sudo`를 제거했다.
  - 이후 실패 3차 원인은 긴 뉴스 AI smoke가 HTTP request timeout을 넘기는 동기 실행 구조였다.
  - `/data-health`의 `recommendation_outcome_*` gate는 AI 장애가 아니라 15개 due 추천 종목의 market price bar가 2026-06-11에 멈춘 가격 데이터 stale 문제였다.
  - alert destination stale 표시는 alert test artifact와 data-health payload가 같은 초 단위로 생성될 때 생기는 작은 clock skew 문제였다.

## What Changed

- `POST /__admin/codex-oauth/smoke/news`는 background job을 시작하고 즉시 `news_smoke_running`을 반환하도록 변경했다.
- Codex OAuth status artifact에 `news_smoke_async_started` running event를 남기고, active running job이 있으면 중복 실행을 막는다.
- `/admin/ai-agents`는 `뉴스 AI 확인 중` 상태를 표시하고 duplicate news smoke 버튼을 비활성화한다.
- alert destination test recency 계산은 5분 이내의 작은 음수 clock skew를 stale로 보지 않는다.
- EC2에서는 stale 가격 15개 종목(`ADI`, `ALAB`, `DIS`, `ELF`, `EROK`, `FANG`, `GILD`, `GOOG`, `INTU`, `LDOS`, `LLY`, `QUBT`, `TGT`, `TSLA`, `XOM`)을 Twelve Data로 2026-06-18까지 보강했다.
- recommendation outcome calibration을 재실행해 `outcome_count=19`, `ready_for_backfill_count=0`, `open_gates=[]`를 확인했다.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest tests.test_codex_oauth_operator tests.test_frontend_api_server tests.test_frontend_live_adapter`
- passed: `git diff --check`
- passed on EC2 runtime: `systemctl --failed` returned 0 failed units.
- passed on EC2 runtime: `/__health`, `/__ready`, `/`, `/data-health`, `/admin/ai-agents`, `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading` returned 200.
- passed on EC2 data-health: `open_gates=[]`, `alert_destination.status=external_destination_verified`, `active_recommendation_price_freshness.status=fresh`, `recommendation_outcome_calibration.status=ready_for_manual_weight_review`, `recommendation_outcome_maturity.status=not_due`.
- passed: deployed commit `9631cef4` to EC2 via `git pull --ff-only origin develop`.
- passed: EC2 `python -m compileall -q src`, `apps/web npm run build`, and restart of `stockanalysis-frontend-api.service` / `stockanalysis-web.service`.
- passed: `POST /__admin/codex-oauth/smoke/news` returned immediately with `status=news_smoke_running` and `background_job_started=true`.
- passed: Codex OAuth background news smoke completed and status returned to `healthy`; latest event `news_smoke`, login probe `Logged in using ChatGPT`.
- passed: local tunnel `http://127.0.0.1:13000` returned 200 for `/`, `/data-health`, `/admin/ai-agents`, `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading`.

## Next Step

- exact next step: monitor next `news-intraday` and next recommendation outcome due window. Do not start manual weight review until a separate approved task opens it.
