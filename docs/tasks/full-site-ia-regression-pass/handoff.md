# Session Handoff

## Current Status

- 상태: in_progress
- in progress: 배포된 EC2 화면을 사용자 동선 기준으로 순회해 IA/문구 회귀를 점검한다.
- 기준일: 2026-05-23

## Investigation

- 이전 패스들에서 홈, 뉴스·AI, 종목/추천/가상 거래, 운영 모니터링 화면을 각각 정리했다.
- 이번 작업은 개별 화면 개선 뒤 생길 수 있는 전체 동선 중복, 남은 내부 용어, 빈 값/에러성 표시를 한 번에 잡는 회귀 패스다.
- 먼저 배포 화면 visible text와 Playwright snapshot을 기준으로 문제를 찾고, 발견된 부분의 최소 파일만 수정한다.

## Mutable Surface

- `apps/web/src/app/**/page.tsx`
- `apps/web/src/components/*`
- `apps/web/src/lib/korean-labels.ts`
- `docs/tasks/full-site-ia-regression-pass/*`

## Exact Next Step

- exact next step: 대표 라우트 visible text 검사를 실행해 에러성/내부 표현/어색한 빈 값을 찾고, 발견한 항목만 수정한다.
