# Task Contract

## Task

- 이름: cockpit-editorial-research-redesign
- 요청: 현재 투자 cockpit UI를 흑백 editorial research terminal 방향으로 1차 전환한다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Next.js cockpit의 공통 shell과 홈 화면이 dark glass bento 스타일에서 벗어나, 번호형 내비게이션, 얇은 선, 큰 리서치형 타이포, 운영 관계도, ledger 중심의 투자 운영 화면으로 보인다.

## Why

- 현재 UI는 읽을 수 있지만 일반 SaaS dashboard/bento 패턴에 가깝다.
- 이 프로젝트의 목적은 장기 투자 판단을 직접 자동화하기보다, thesis, evidence, cycle, remediation 상태를 검증 가능한 운영 체계로 해석하는 것이다.
- 디자인도 그 정체성을 보여줘야 하므로, 장식적인 카드보다 리서치 노트와 운영 인덱스에 가까운 정보 구조가 필요하다.

## Scope

- 포함:
  - `apps/web` 공통 shell의 visual language 갱신
  - 홈 dashboard 레이아웃의 editorial/index/matrix 스타일 전환
  - 기존 data fetching/API DTO/route 구조 유지
  - 기존 한국어 label helper 사용 유지
  - desktop/mobile 브라우저 확인
- 제외:
  - backend API, schema, scoring, benchmark, evaluation 기준 변경
  - 투자 추천 판단 로직 변경
  - 실거래/브로커/order flow
  - host scheduler activation
  - 모든 상세 페이지의 완전한 redesign

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/cockpit-editorial-research-redesign/`
- 수정 금지 파일:
  - `.env`
  - `db/migrations/`
  - backend scoring/schema/evaluation logic
  - broker/order flow
  - host LaunchAgents or scheduler activation files

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - local Next.js dev server route check
  - browser screenshot check for desktop and mobile
  - `git diff --check`

## Done Criteria

- [x] 홈 화면이 새 editorial research terminal 스타일로 렌더링된다.
- [x] 공통 navigation/shell이 번호형 운영 인덱스 문법을 사용한다.
- [x] desktop/mobile 화면에서 핵심 텍스트가 겹치지 않는다.
- [x] `apps/web` typecheck/build를 수행한다.
- [x] task handoff에 검증 결과와 남은 위험을 기록한다.
