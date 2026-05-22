# Task Contract

## Task

- 이름: ai-evidence-macro-candidate-split
- 요청: 종목이 없는 거시/테마 뉴스 후보가 개별 종목 후보처럼 보이는 혼동을 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/ai-evidence`는 직접 종목 후보와 상위 흐름 후보를 분리해서 보여준다.
  - `/events`는 기본 판단 목록에서 직접 종목 후보와 종목 없는 상위 흐름 후보를 다른 섹션으로 보여준다.
  - 종목 없는 Fed/거시 뉴스는 오류가 아니라 상위 흐름 후보로 설명된다.

## Scope

- 포함:
  - `/ai-evidence` information architecture 개선
  - `/events` candidate section 분리
  - 한국어 문구 보강
  - frontend type/build/browser smoke
- 제외:
  - DB migration
  - AI extraction schema 변경
  - recommendation scoring 변경
  - scheduler cadence 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `docs/tasks/ai-evidence-macro-candidate-split/*`
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
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-macro-candidate-split`
  - Browser smoke for `/events`, `/ai-evidence`

## Done Criteria

- [x] Direct stock candidates and macro/theme-only candidates are visually separated.
- [x] Macro/no-symbol candidates are described as upper-level flow candidates, not as broken stock rows.
- [x] Local verification and AWH pass.
- [x] EC2 deploy and browser smoke pass.
