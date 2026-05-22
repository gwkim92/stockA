# Task Contract

## Task

- 이름: frontend-ai-news-cluster-default-date
- 요청: 뉴스·AI 묶음 API가 운영자가 직접 점검하기 쉬운 기본 날짜 동작을 갖게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai/news-clusters?limit=10`이 501이 아니라 최신 기준일 기본값으로 정상 응답한다.
  - 기존 `/api/ai/news-clusters?asOfDate=YYYY-MM-DD&limit=N` 동작은 유지한다.
  - `/intelligence` 화면은 계속 정상 렌더링된다.

## Scope

- 포함:
  - AI 뉴스 묶음 live adapter의 `asOfDate` optional default 처리
  - pagination collection spec에서 AI 뉴스 묶음의 `limit/cursor` 단독 사용 허용
  - focused unit tests
  - local/EC2 smoke
- 제외:
  - 뉴스 clustering 알고리즘 변경
  - AI 호출/스케줄러 주기 변경
  - 추천 점수 산식 변경
  - DB schema 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_frontend_pagination.py`
  - `docs/tasks/frontend-ai-news-cluster-default-date/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler systemd units

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_frontend_pagination`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-ai-news-cluster-default-date`
  - EC2 authorized smoke for `/api/ai/news-clusters?limit=10`

## Done Criteria

- [ ] `resolve_live_frontend_response("/api/ai/news-clusters?limit=10")` returns data with today/default `as_of_date`.
- [ ] SQL pagination still uses `limit + 1`.
- [ ] EC2 API returns 200 for `/api/ai/news-clusters?limit=10`.
