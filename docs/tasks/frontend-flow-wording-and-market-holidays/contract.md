# Task Contract

## Task

- 이름: frontend-flow-wording-and-market-holidays
- 요청: 화면 문구와 배치를 점검하고, 사용자가 시스템 흐름을 이해할 수 있게 만들며, 최신 완료 미국 거래일 정책에 필요한 2026년 휴장일을 실행 env에 추가한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 로컬 live MVP 화면은 데이터 수집, 정규화, 운영 점검, 신호/논리 생성, 사람 검토, 성과 측정의 흐름을 첫 화면에서 설명한다.
  - 주요 페이지의 영어/개발자식 워딩을 운영자 관점의 한국어로 정리한다.
  - repo 밖 data operations env에는 2026년 미국장 full-closure 휴장일이 설정되어 scheduler freshness 계산이 휴장일을 건너뛸 수 있다.

## Why

- 현재 화면은 개별 데이터는 보여주지만, 처음 보는 사용자가 전체 시스템이 어떤 순서로 작동하는지 파악하기 어렵다.
- 일부 라벨은 `Review Queue`, `Runtime Ledger`, `instruments`, `Event/Momentum/Quality`처럼 영어 또는 내부 구현 용어가 섞여 있다.
- 최신 완료 미국 거래일 정책은 휴장일 목록이 repo 밖 env에 들어가야 실제 scheduler 운용에서 provider 호출 낭비를 줄일 수 있다.

## Scope

- 홈 화면에 시스템 운영 플로우를 추가한다.
- 상단 네비게이션, 홈, 데이터 상태, 사이클, 이벤트, 테마, 추천, 투자 논리, 포트폴리오 커버리지, 성과, AI 증거, 원천 문서 페이지의 문구를 점검하고 필요한 범위만 수정한다.
- `/private/tmp/stockanalysis-runtime/data-operations.real.env`에 휴장일과 freshness policy env를 추가한다.
- Next.js typecheck/build와 주요 라우트 HTTP smoke를 실행한다.

## Boundaries

- DB schema, scoring, benchmark, evaluation split은 바꾸지 않는다.
- 실제 broker/order flow, write API, RBAC, scheduler host activation은 구현하지 않는다.
- `.env`나 provider API key 값을 출력하지 않는다.
- 외부 holiday API를 추가하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/themes/[themeKey]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/performance/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/source-documents/[documentId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/frontend-flow-wording-and-market-holidays/*`
  - `/private/tmp/stockanalysis-runtime/data-operations.real.env`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - 주요 라우트 HTTP 200 smoke
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-flow-wording-and-market-holidays`
  - `git diff --check`

## Done Criteria

- [x] 실행 env에 2026년 미국장 휴장일이 추가된다.
- [x] 홈 화면이 시스템 플로우를 설명한다.
- [x] 주요 페이지 워딩이 한국어 운영 화면 기준으로 정리된다.
- [x] 화면 라우트가 200으로 렌더링된다.
- [x] 검증 결과와 남은 리스크가 handoff/review에 기록된다.
