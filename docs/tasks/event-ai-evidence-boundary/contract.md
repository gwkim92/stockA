# Task Contract

## Task

- 이름: event-ai-evidence-boundary
- 요청: `/events`와 `/ai-evidence`에서 `news_cluster_summary`가 `news_event_candidate`처럼 보이는 혼선을 제거한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 이벤트 원장은 개별 뉴스 AI 후보와 뉴스 묶음 증거를 구분해서 보여준다.
  - 이벤트에 `news_event_candidate`와 `news_cluster_summary`가 모두 있으면 개별 후보를 우선 노출한다.
  - AI 후보 목록 `/ai-evidence`는 개별 `news_event_candidate`만 목록으로 보여준다.
  - 뉴스 묶음은 `/intelligence`에서 확인하라는 경로가 명확하다.

## Scope

- 포함:
  - event list live adapter의 evidence 선택 우선순위 수정
  - event list summary에 `news_event_candidate_count`, `news_cluster_summary_count` 추가
  - event list API에 `evidenceType` filter 추가
  - `/events` 문구와 metric 카드 정리
  - `/ai-evidence` index가 cluster summary를 후보 목록에 섞지 않도록 수정
  - focused tests와 EC2 smoke
- 제외:
  - DB schema 변경
  - 추천 점수 산식 변경
  - 뉴스 수집 provider 변경
  - 실거래 또는 주문 자동화

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/event-ai-evidence-boundary/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units
  - recommendation scoring weights

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task event-ai-evidence-boundary`
  - EC2 `/api/events?...` smoke
  - EC2 `/events`, `/ai-evidence` render smoke

## Done Criteria

- [x] SQL evidence selection prefers `news_event_candidate` over `news_cluster_summary`.
- [x] `/events` metrics separate individual AI candidates from cluster evidence.
- [x] `/ai-evidence` list excludes cluster summary cards.
- [x] `/ai-evidence` uses `evidenceType=news_event_candidate` and does not depend on the latest unfiltered events page.
- [x] EC2 pages render without server component error.
