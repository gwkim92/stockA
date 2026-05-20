# Data Automation Status Summary Plan

## Goal

- `/data-health`에서 주식 캔들 수집, 뉴스 수집, AI 분석이 최근 실행됐는지와 실제 반복 자동화가 켜졌는지 구분해서 보여준다.

## Scope

- 포함:
  - existing data-health DTO의 `pipeline_runs`와 `scheduler.activation`을 사용한다.
  - market-price-daily, news-rss-daily, event-intelligence-weekly 상태 요약을 한국어로 표시한다.
  - "최근 실행 성공"과 "반복 자동화 꺼짐/승인 대기"를 분리해 표시한다.
  - task docs와 verification evidence를 남긴다.
- 제외:
  - backend DTO/API 변경
  - DB migration
  - scheduler host activation
  - provider/feed/env 변경
  - live LLM/provider call
  - scoring/trading/order 변경

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- browser smoke for `/data-health`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-automation-status-summary`
- `git diff --check`
