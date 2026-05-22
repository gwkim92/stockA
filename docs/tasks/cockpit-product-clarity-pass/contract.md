# Task Contract

## Task

- 이름: cockpit-product-clarity-pass
- 요청: 첫 화면과 주요 운영 화면에서 사용자가 무엇을 봐야 하는지 명확히 하고, 중복되는 기능 지도와 개발자용 문구를 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 첫 화면은 “수집 정상 여부 -> 뉴스/종목 영향 -> 추천/거래 안전” 순서가 명확하다.
  - Paper 거래 화면은 현재가 실거래인지, paper 검증인지, 무엇이 막고 있는지 바로 보여준다.
  - 데이터 수집 화면은 사용자 판단 요약을 먼저 보여주고 운영자 로그는 상세 영역으로 분리한다.
  - 뉴스 AI 화면은 뉴스가 왜 묶였고 어떤 종목/테마와 연결되는지 먼저 설명한다.
  - API contract, DB schema, 추천 산식, broker/order flow는 변경하지 않는다.

## Scope

- Next.js cockpit 화면 문구와 정보 구조를 정리한다.
- 첫 slice는 `/`, `/paper-trading`, 공통 뉴스 카드 문구에 집중한다.
- 두 번째 slice는 `/data-health`, `/intelligence`에 집중한다.
- API contract, DB schema, 추천 산식, broker/order flow는 변경하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/components/news-event-card.tsx`
  - `docs/tasks/cockpit-product-clarity-pass/*`
- 수정 금지 파일:
  - DB migrations/schema
  - backend API contract
  - scheduler cadence
  - secrets/env files
  - recommendation scoring
  - broker/order flow

## Acceptance Criteria

- 첫 화면은 “수집 정상 여부 -> 뉴스/종목 영향 -> 추천/거래 안전” 순서가 명확하다.
- 첫 화면에서 같은 성격의 카드 목록이 반복되지 않는다.
- Paper 거래 화면은 현재가 실거래인지, paper 검증인지, 무엇이 막고 있는지 바로 보여준다.
- 뉴스 카드에서 종목이 없는 거시/테마 뉴스는 “종목 미분류”가 아니라 “시장/테마 뉴스”로 표현한다.
- 데이터 수집 화면은 수집/자동화/API 예산 판단을 먼저 보여주고, 운영자용 상세는 접힘 패널로 분리한다.
- 뉴스 AI 화면은 묶인 기준, 종목 관계, 추천 영향을 각 뉴스 묶음에서 설명한다.
- Next typecheck/build와 EC2 route smoke가 통과한다.

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cockpit-product-clarity-pass`
  - EC2 route smoke: `/`, `/data-health`, `/intelligence`, `/events`, `/ai-evidence`, `/stocks`, `/recommendations`, `/paper-trading`, `/trading-readiness`

## Non-goals

- 실거래 연결, broker submission, 주문 실행.
- 추천 품질 산식 변경.
- 뉴스 AI/RAG pipeline 구조 변경.
- 전체 페이지 디자인 전면 재작성.
