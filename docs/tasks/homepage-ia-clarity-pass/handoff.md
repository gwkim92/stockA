# Session Handoff

## Current Status

- 상태: in_progress
- in progress: `/` 첫 화면의 정보 구조와 사용자-facing 문구를 정리 중이다.
- 기준일: 2026-05-23

## Investigation

- 첫 화면은 이미 “오늘의 운용 순서” 구조가 있으나 `파이프라인`, `뉴스 원장` 같은 내부 표현이 남아 있다.
- hero와 하단 “오늘의 핵심 판단”이 일부 중복되어, 사용자가 첫 화면에서 무엇을 눌러야 하는지 더 선명하게 만들 필요가 있다.
- 현재 가장 중요한 사용 흐름은 `수집 상태 확인 → 뉴스/AI 근거 확인 → 영향 종목 확인 → 추천/보유 검토 → 거래 안전 확인`이다.

## Mutable Surface

- `apps/web/src/app/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/homepage-ia-clarity-pass/*`

## Exact Next Step

- exact next step: `apps/web/src/app/page.tsx`에서 첫 화면의 결론/다음 행동/점검 순서 문구를 재구성하고, 필요한 CSS를 보강한 뒤 로컬 typecheck/build/AWH와 EC2 route smoke를 진행한다.
