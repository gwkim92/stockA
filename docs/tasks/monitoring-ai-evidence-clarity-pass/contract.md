# Task Contract

## Task

- 이름: monitoring-ai-evidence-clarity-pass
- 요청: 수집 상태, 뉴스 1차 분류, AI 후보/결과/차단 화면의 개발자·운영자 용어를 사용자 판단 흐름 중심으로 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: `/data-health`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`가 개발자 로그가 아니라 사용자가 수집 상태, 뉴스 분류, AI 후보, 통과 결과, 차단 후보를 판단할 수 있는 한국어 화면으로 동작한다.
- `/data-health`는 운영 로그가 아니라 “무엇이 자동으로 돌고, 최신인지, 문제가 있으면 무엇을 먼저 봐야 하는지”를 먼저 보여준다.
- `/events/classification`은 LLM/내부 태그 표현보다 1차 분류가 무엇이고 왜 검수해야 하는지 보여준다.
- `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`는 후보, 통과, 차단의 차이를 명확히 보여준다.
- DB/API response shape, 수집 실행, AI 실행, 추천 산식, scheduler 설정은 바꾸지 않는다.

## Scope

- 포함:
  - 사용자-facing 문구 정리
  - 화면 switchboard/summary label 정리
  - operator details 안의 노출 문구 일부 정리
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - API contract 변경
  - 데이터 삭제/재수집
  - AI provider/runtime 변경
  - scheduler/timer 설정 변경

## Mutable Surface

- mutable surface: `apps/web/src/app/data-health/page.tsx`, `apps/web/src/app/events/classification/page.tsx`, `apps/web/src/app/ai-evidence/page.tsx`, `apps/web/src/app/ai-evidence/results/page.tsx`, `apps/web/src/app/ai-evidence/blocked/page.tsx`, `apps/web/src/components/news-event-card.tsx`, `apps/web/src/lib/korean-labels.ts`, `docs/tasks/monitoring-ai-evidence-clarity-pass/*`.
- 수정 가능:
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/events/classification/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/components/news-event-card.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/monitoring-ai-evidence-clarity-pass/*`
- 수정 금지:
  - `.env`
  - DB migrations/schema
  - backend route contract
  - scheduler units/timers
  - recommendation scoring weights

## Acceptance Criteria

- 일반 화면 전면에서 `LLM`, `validator`, `artifact`, `smoke`, `stderr`, `gate`, `pipeline`, `provider` 같은 내부 단어가 보이지 않는다.
- 모니터링 화면은 수집/분석/추천/보유검토 상태를 “사용자 확인 순서”로 설명한다.
- AI 화면은 후보, 통과 결과, 차단 목록이 서로 다른 의미임을 설명한다.
- Next typecheck/build, AWH verify, EC2 route smoke가 통과한다.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task monitoring-ai-evidence-clarity-pass`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task monitoring-ai-evidence-clarity-pass`
- EC2 route smoke: `/data-health`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`
