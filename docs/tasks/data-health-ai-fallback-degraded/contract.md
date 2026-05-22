# Task Contract

## Task

- 이름: data-health-ai-fallback-degraded
- 요청: `news-ai-evidence`가 fallback으로 끝났을 때 자동화 성공처럼 숨기지 말고 `/data-health`에서 품질 저하로 표시한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `news-rss-ai-extract-run`에서 후보 실패가 있으면 `ops.pipeline_run.status`가 `succeeded_with_fallback`으로 남는다.
  - `/api/data-health`는 `succeeded_with_fallback`을 `health_status=degraded`로 반환한다.
  - `/data-health`는 AI 분석이 “성공했지만 fallback 사용” 상태임을 사람이 이해할 수 있게 표시한다.

## Scope

- 포함:
  - news AI runner pipeline status 변경
  - data-health SQL health mapping 변경
  - Next `/data-health` 문구/위험도 표시 보강
  - tests와 task handoff 갱신
- 제외:
  - DB migration
  - scheduler 주기 변경
  - Codex OAuth 인증 변경
  - 추천 점수 산식 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_news_rss_ai_extract.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/data-health-ai-fallback-degraded/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler unit/timer files
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task data-health-ai-fallback-degraded`
  - EC2 API/browser smoke for `/api/data-health` and `/data-health`

## Done Criteria

- [x] AI fallback pipeline status is stored as `succeeded_with_fallback`.
- [x] Data-health maps fallback status to `degraded`.
- [x] Frontend explains fallback status clearly.
- [x] Local verification and AWH pass.
- [x] EC2 deploy and smoke pass.
