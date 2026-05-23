# Task Contract

## Task

- 이름: decision-page-copy-clarity-pass
- 요청: 추천, 뉴스·AI, 가상 거래 화면의 운영자/개발자용 문구를 사용자 판단 흐름 중심으로 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/recommendations`는 추천 후보를 “왜 봐야 하는지”와 다음 확인 화면 중심으로 설명한다.
  - `/intelligence`는 artifact/LLM/cluster 같은 내부 표현보다 수집, AI 분석, 검증, 추천 연결 상태를 먼저 보여준다.
  - `/paper-trading`은 paper 후보가 테스트인지, 실제 주문 가능한 상태인지, 무엇이 막고 있는지 명확히 보여준다.
  - DB/API/추천 산식/scheduler/broker 동작은 변경하지 않는다.

## Scope

- 포함:
  - 사용자-facing 문구와 카드 설명 정리
  - 숨김 metadata summary/label 일부 정리
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - API response contract 변경
  - 추천 점수 계산 변경
  - AI pipeline 재실행
  - 실제 주문/브로커 연동 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/decision-page-copy-clarity-pass/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - backend API contract
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Acceptance Criteria

- 세 화면 상단과 핵심 카드에 “뭘 봐야 하는지”가 먼저 나온다.
- `artifact`, `runner`, `rule code`, `source_run_id` 같은 내부 단어가 일반 화면 전면에 나오지 않는다.
- 가상 거래 화면은 “paper 후보”, “브로커 제출 0건”, “실거래 차단/조건”을 명확히 구분한다.
- Next typecheck/build와 route smoke가 통과한다.

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-page-copy-clarity-pass`
  - EC2 route smoke: `/intelligence`, `/recommendations`, `/recommendations/recommendation-64`, `/paper-trading`
