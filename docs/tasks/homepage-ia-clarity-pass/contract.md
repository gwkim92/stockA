# Task Contract

## Task

- 이름: homepage-ia-clarity-pass
- request: 첫 화면에서 사용자가 “오늘 무엇을 봐야 하는지”를 바로 이해하게 만들고, 수집/뉴스 AI/종목/추천 보유/거래 안전으로 이어지는 판단 순서를 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: `/` 첫 화면이 운영자 로그나 기능 나열이 아니라 오늘의 판단 순서, 현재 결론, 다음 행동을 한국어로 명확히 보여준다.
- 데이터 수집, 뉴스 AI, 종목 영향, 추천/보유, 거래 안전의 진입점이 한 화면에서 구분된다.
- 사용자-facing 영역에서 `파이프라인`, `원장`, 내부 런타임 표현을 제거한다.

## Scope

- 포함:
  - `apps/web/src/app/page.tsx` 첫 화면 IA와 문구 정리
  - 필요한 최소 CSS 보강
  - task handoff/review
- 제외:
  - DB/API contract 변경
  - 데이터 수집/AI/scheduler 동작 변경
  - 추천 산식 변경
  - 다른 상세 페이지 리디자인

## Mutable Surface

- mutable surface: `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`, `docs/tasks/homepage-ia-clarity-pass/*`.
- 수정 금지:
  - `.env`
  - backend API response shape
  - DB schema/migrations
  - scheduler units/timers
  - recommendation scoring

## Acceptance Criteria

- 첫 화면 hero가 현재 결론과 다음 행동을 즉시 보여준다.
- 점검 순서는 `수집 → 뉴스/AI → 종목 → 추천/보유 → 거래 안전`으로 읽힌다.
- 첫 화면 visible text에 `파이프라인`, `뉴스 원장`, `LLM`, `validator`, `artifact`, `smoke`, `stderr`, `systemd`, `Postgres`가 노출되지 않는다.
- `/` 라우트가 EC2에서 200으로 렌더링된다.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task homepage-ia-clarity-pass`
- verification command: EC2 `/` route smoke and Playwright snapshot
