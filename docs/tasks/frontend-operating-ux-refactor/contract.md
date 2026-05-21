# Task Contract

## Task

- 이름: frontend-operating-ux-refactor
- 요청: 전체 화면을 점검하고, 무엇을 보여주려는지 이해하기 어렵고 문구/줄바꿈이 어색한 문제를 운영 플로우 중심으로 리팩터링한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 사용자가 헤더와 핵심 화면에서 `데이터 수집 -> 뉴스/AI 분석 -> 종목/추천/보유검토 -> 거래 안전/성과` 흐름을 이해할 수 있고, 개별 뉴스 후보 분석 위치와 의미가 화면에서 명확하게 드러난다.

## Findings

- 헤더가 15개 링크를 동일 위계로 노출해 사용자가 어디서 무엇을 봐야 하는지 판단하기 어렵다.
- 큰 한글 제목이 과도하게 커서 줄바꿈이 임의로 끊기고, 일부 영어/식별자가 카드 밖으로 밀릴 위험이 있다.
- `/events` 문구가 “다음 enrichment 단계에서 붙인다”처럼 현재 구현과 맞지 않는 표현을 포함한다.
- `/intelligence`는 데이터가 많지만 “뉴스 묶음”과 “개별 뉴스 AI 후보”의 역할 차이가 즉시 보이지 않는다.
- `/ai-evidence/:id`는 개별 뉴스 후보 분석을 보여주지만, 사용자가 이 화면을 어디서 찾아야 하는지 약하다.

## Scope

- 포함:
  - 전역 헤더 내비게이션을 운영 흐름별 그룹으로 재구성
  - 전역 타이포그래피, 줄바꿈, 오버플로우 hardening
  - 주요 페이지 hero/설명 문구 정리
  - `/events`, `/intelligence`, `/ai-evidence/:id`에서 뉴스 AI 후보 분석 위치와 역할을 명확히 표시
  - 브라우저 smoke와 Next type/build 검증
- 제외:
  - DB schema 변경
  - API DTO 변경
  - 추천 산식 변경
  - 신규 차트 구현
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/remediation/page.tsx`
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/frontend-operating-ux-refactor/`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - backend scoring/recommendation logic
  - scheduler/systemd files
  - broker/order submission code

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task frontend-operating-ux-refactor`
  - `agent-browser` smoke for `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence/<news_event_candidate>`, `/recommendations`, `/stocks`

## Done Criteria

- [ ] 헤더가 기능 나열이 아니라 운영 흐름별 그룹으로 보인다.
- [ ] 주요 페이지 제목/설명이 과도하게 깨지지 않는다.
- [ ] 개별 뉴스 AI 후보 분석이 `/events -> AI 후보 링크 -> /ai-evidence/:id` 흐름으로 설명된다.
- [ ] `/intelligence`에서 뉴스 묶음과 개별 AI 후보의 차이가 명확하다.
- [ ] Next typecheck/build와 브라우저 smoke를 통과한다.
