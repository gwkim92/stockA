# Session Handoff

## Current Status

- 상태: in_progress
- in progress: 수집, AI 분석, 차단 후보, 거래 안전 화면을 사용자용 운영 모니터링 흐름으로 정리한다.
- 기준일: 2026-05-23

## Investigation

- 이전 패스에서 뉴스 판단, 종목 상세, 추천 상세, 가상 거래의 사용자-facing 문구는 정리했다.
- 남은 모니터링 화면은 아직 `수집/분석/차단/거래 안전`이 한 흐름으로 읽히는지 확인해야 한다.
- 특히 운영자 로그처럼 보이는 표현, 내부 런타임 표현, 개발자용 링크 라벨을 제거해야 한다.

## Mutable Surface

- `apps/web/src/app/data-health/page.tsx`
- `apps/web/src/app/ai-evidence/results/page.tsx`
- `apps/web/src/app/ai-evidence/blocked/page.tsx`
- `apps/web/src/app/trading-readiness/page.tsx`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/operations-monitoring-flow-clarity-pass/*`

## Exact Next Step

- exact next step: 네 화면의 visible text와 링크 라벨을 점검하고, 내부 용어를 사용자 문장으로 바꾼 뒤 로컬/EC2 검증을 실행한다.
