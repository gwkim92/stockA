# Task Contract

## Task

- 이름: news-information-architecture-split
- 요청: 홈의 `수집 뉴스 원장`, `1차 분류 태그`, `분석 목록`, `구조화 결과`가 같은 화면처럼 보이는 문제를 고치고, 각 화면을 어떻게 봐야 하는지 명확하게 만든다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 홈 기능 지도에서 뉴스 수집/분류/AI 분석/구조화 결과/차단 후보가 서로 다른 목적과 경로를 가진다.
  - `/events`는 수집 원장 전용 화면으로 동작한다.
  - `/events/classification`은 1차 분류 태그 전용 화면으로 동작한다.
  - `/ai-evidence/results`는 통과한 구조화 결과 전용 화면으로 동작한다.
  - `/ai-evidence/blocked`는 validator 차단/저신호 보류 후보 전용 화면으로 동작한다.
  - 각 화면 상단에 “무엇을 봐야 하는지”가 사람 언어로 명확히 표시된다.

## Scope

- 포함:
  - Next.js page routing 추가/수정
  - 뉴스 이벤트 카드 공통 컴포넌트 추가
  - 홈 기능 지도 링크와 UX 문구 수정
  - 타입체크/빌드 검증
  - EC2 배포 확인
- 제외:
  - DB schema 변경
  - 백엔드 API contract 변경
  - AI 추출 로직 변경
  - 추천 점수 산식 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/events/classification/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/components/*`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/news-information-architecture-split/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - backend canonical API contract
  - scheduler/runtime secrets

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-information-architecture-split`

## Done Criteria

- [x] 홈의 뉴스 관련 기능 링크가 서로 다른 전용 화면으로 간다.
- [x] `/events`가 원장 화면으로 읽힌다.
- [x] `/events/classification`이 1차 태그 화면으로 읽힌다.
- [x] `/ai-evidence/results`가 구조화 결과 화면으로 읽힌다.
- [x] `/ai-evidence/blocked`가 차단 후보 화면으로 읽힌다.
- [x] 로컬 검증과 EC2 smoke가 통과한다.
