# Task Contract

## Task

- 이름: event-candidate-quality-summary
- 요청: 뉴스 AI 후보 목록에서 숨겨진 저신호 후보의 존재와 이유를 화면/API에서 이해 가능하게 표시한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/events?evidenceType=news_event_candidate` summary가 숨겨진 legacy low-signal candidate 수를 제공한다.
  - `/events`와 `/ai-evidence`가 “후보가 왜 적게 보이는지”를 한국어로 설명한다.
  - 기존 raw ledger, AI 상세, 추천 점수, DB schema는 변경하지 않는다.

## Scope

- 포함:
  - frontend live adapter event list SQL summary 보강
  - TypeScript contract 보강
  - `/events`, `/ai-evidence` 문구 개선
  - focused regression tests
- 제외:
  - DB migration
  - artifact 삭제/update
  - scheduler cadence 변경
  - recommendation scoring 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `docs/tasks/event-candidate-quality-summary/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task event-candidate-quality-summary`
  - EC2 API smoke for `/api/events?evidenceType=news_event_candidate`

## Done Criteria

- [x] API summary includes `suppressed_low_signal_candidate_count`.
- [x] Count is only applied to `news_event_candidate` candidate view, not raw ledger.
- [x] `/events` and `/ai-evidence` explain hidden low-signal candidates in human-readable Korean.
- [x] Local verification and AWH pass.
- [x] EC2 API smoke confirms the new summary field.
