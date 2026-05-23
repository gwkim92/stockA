# Session Handoff

## Current Status

- 상태: in_progress
- current status: in_progress
- 진행 중: 추천, 뉴스·AI, 가상 거래 화면의 사용자-facing 문구를 판단 흐름 중심으로 정리한다.
- 기준일: 2026-05-23

## Investigation

- `/recommendations`의 운영 흐름에는 `스케줄러`, `Postgres` 같은 내부 구현 문구가 전면에 나온다.
- `/intelligence`에는 `artifact`, `LLM`, `cluster`, `provider` 중심 표현이 섞여 있어 사용자가 “뉴스 수집, AI 분석, 검증, 추천 연결” 상태를 바로 읽기 어렵다.
- `/paper-trading`은 paper 후보와 실제 주문 가능 상태의 구분은 있으나, “현재 무엇이 되는지/안 되는지”를 더 직접적으로 보여줄 필요가 있다.

## Mutable Surface

- `apps/web/src/app/recommendations/page.tsx`
- `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- `apps/web/src/app/intelligence/page.tsx`
- `apps/web/src/app/paper-trading/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/decision-page-copy-clarity-pass/*`

## Exact Next Step

- exact next step: 세 화면의 상단/핵심 카드 문구를 수정하고 로컬/EC2에서 route smoke와 Playwright snapshot으로 확인한다.
