# Task Contract

## Task

- 이름: operations-monitoring-flow-clarity-pass
- request: 수집, AI 분석, 차단 후보, 거래 안전 화면을 사용자용 운영 모니터링 흐름으로 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: 사용자가 `수집 상태 → AI 분석 결과 → 차단/통과 후보 → 거래 안전 상태`를 한 흐름으로 이해한다.
- `/data-health`는 운영자 로그가 아니라 “무엇이 자동으로 돌고 있고 어디가 막혔는지”를 보여준다.
- `/ai-evidence/results`는 AI가 구조화한 결과와 추천 입력 가능 여부를 보여준다.
- `/ai-evidence/blocked`는 차단/보류된 후보와 이유, 다음 조치를 보여준다.
- `/trading-readiness`는 실거래 가능 여부와 차단 조건을 사용자가 바로 이해하게 한다.

## Scope

- 포함:
  - `/data-health` 사용자-facing 문구와 CTA 정리
  - `/ai-evidence/results` 문구와 결과 해석 흐름 정리
  - `/ai-evidence/blocked` 차단 이유/다음 조치 문구 정리
  - `/trading-readiness` 안전 상태 문구와 링크 라벨 정리
  - 공용 한국어 라벨 보강
  - task handoff/review
- 제외:
  - API response shape 변경
  - DB schema/migration
  - scheduler 실행 주기 변경
  - AI provider runtime 변경
  - broker/order execution logic 변경

## Mutable Surface

- mutable surface: `apps/web/src/app/data-health/page.tsx`, `apps/web/src/app/ai-evidence/results/page.tsx`, `apps/web/src/app/ai-evidence/blocked/page.tsx`, `apps/web/src/app/trading-readiness/page.tsx`, `apps/web/src/lib/korean-labels.ts`, `docs/tasks/operations-monitoring-flow-clarity-pass/*`.
- 수정 금지:
  - `.env`
  - backend API contracts
  - DB migrations/schema
  - scheduler/timer 설정
  - broker/order execution logic

## Acceptance Criteria

- `/data-health` visible text explains collection freshness, automation state, provider budget, and next action without exposing `pipeline`, `systemd`, `Postgres`, `stderr`, `artifact`, `smoke`.
- `/ai-evidence/results` visible text explains AI extracted outputs and whether they can feed recommendations without exposing `validator`, `LLM`, `artifact`, `RAG`.
- `/ai-evidence/blocked` visible text explains blocked/suppressed candidates and next action without exposing `validator`, `LLM`, `artifact`, `stderr`.
- `/trading-readiness` visible text explains broker submission state, paper-only mode, kill switch/order limits/account permission, and next action without exposing internal runtime terms.

## Verification Commands

- verification command: `git diff --check`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task operations-monitoring-flow-clarity-pass`
- verification command: EC2 route smoke for `/data-health`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/trading-readiness`
- verification command: Playwright snapshot text check for the same routes
