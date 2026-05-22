# Task Contract

## Task

- 이름: candidate-card-wording-cleanup
- 요청: 후보 카드 내부의 버튼명, 상태 설명, 빈 상태 문구를 후보 종류별로 명확하게 분리한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 직접 종목 후보는 “종목 AI 근거”로 표시된다.
  - 상위 흐름 후보는 “흐름 AI 근거”로 표시된다.
  - 상위 흐름 후보에서 “개별 AI 후보”처럼 보이는 문구를 제거한다.
  - 관련 이벤트가 없을 때 직접 종목 후보와 상위 흐름 후보의 빈 상태 문구가 다르다.

## Scope

- 포함:
  - `/events` 후보 카드 문구 정리
  - `/ai-evidence` 후보 카드 버튼/칩 문구 정리
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - API contract 변경
  - AI extraction schema 변경
  - recommendation scoring 변경
  - scheduler cadence 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `docs/tasks/candidate-card-wording-cleanup/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task candidate-card-wording-cleanup`
  - Browser smoke for `/events`, `/ai-evidence`

## Done Criteria

- [x] `/events` no longer uses generic `개별 AI 후보` for macro/theme-only candidates.
- [x] `/ai-evidence` uses candidate-specific detail button labels.
- [x] Empty relationship text differs for direct stock candidates and macro/theme candidates.
- [x] Local verification and AWH pass.
- [ ] EC2 deploy and browser smoke pass.
