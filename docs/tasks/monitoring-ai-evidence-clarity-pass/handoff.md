# Session Handoff

## Current Status

- 상태: in_progress
- current status: in_progress
- 진행 중: 수집 상태와 뉴스 AI 근거 화면의 사용자-facing 문구를 정리한다.
- 기준일: 2026-05-23

## Investigation

- `/data-health`는 상단 요약은 개선되어 있으나 상세 summary와 일부 카드에 `LLM`, `validator`, `artifact`, `smoke`, `stderr`, `gate`, `pipeline`, `systemd`, `Postgres` 같은 내부 표현이 남아 있다.
- `/events/classification` switchboard에 `LLM 후보 확인`이 노출되어 있고, 1차 분류가 “AI 전 검수 단계”라는 설명이 더 선명해야 한다.
- `/ai-evidence`와 하위 화면은 후보/통과/차단의 의미는 있으나 `validator`, `confidence gate`, `provider` 같은 내부 용어가 남아 있다.

## Mutable Surface

- `apps/web/src/app/data-health/page.tsx`
- `apps/web/src/app/events/classification/page.tsx`
- `apps/web/src/app/ai-evidence/page.tsx`
- `apps/web/src/app/ai-evidence/results/page.tsx`
- `apps/web/src/app/ai-evidence/blocked/page.tsx`
- `apps/web/src/components/news-event-card.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/monitoring-ai-evidence-clarity-pass/*`

## Exact Next Step

- exact next step: 위 화면들의 내부 용어를 사용자 용어로 바꾸고, 로컬 typecheck/build/AWH 후 EC2에 배포해 route smoke를 확인한다.
