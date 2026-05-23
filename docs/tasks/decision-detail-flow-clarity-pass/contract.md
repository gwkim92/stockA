# Task Contract

## Task

- 이름: decision-detail-flow-clarity-pass
- request: 종목 상세, 추천 상세, 가상 거래 화면에서 사용자가 무엇을 봐야 하는지 명확히 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- goal: `뉴스/상위 흐름 → 종목 영향 → 추천 점수 → 보유 검토 → 가상 거래 상태`가 화면에서 끊기지 않고 읽힌다.
- 사용자는 종목 상세에서 가격, 직접 뉴스, 상위 흐름, 추천/보유 연결을 구분할 수 있다.
- 사용자는 추천 상세에서 점수 재료가 가격/순위, 직접 뉴스/AI, 상위 흐름, 보유검토 중 어디서 왔는지 구분할 수 있다.
- 사용자는 가상 거래 화면에서 “테스트 중인지, 실제 주문 가능한지, 무엇이 막고 있는지”를 즉시 이해할 수 있다.

## Scope

- 포함:
  - `/stocks/[symbol]` 문구, 섹션 제목, 링크 라벨 정리
  - `/recommendations/[id]` 문구, 근거 링크 라벨, 읽는 순서 정리
  - `/paper-trading` 문구, 단계 설명, 안전 상태 정리
  - 공용 한국어 라벨의 사용자-facing 표현 보강
  - task handoff/review
- 제외:
  - API response shape 변경
  - DB schema/migration
  - 추천 산식 변경
  - 가상/실거래 실행 로직 변경
  - scheduler/AI runtime 변경

## Mutable Surface

- mutable surface: `apps/web/src/app/stocks/[symbol]/page.tsx`, `apps/web/src/app/recommendations/[recommendationId]/page.tsx`, `apps/web/src/app/paper-trading/page.tsx`, `apps/web/src/lib/korean-labels.ts`, `docs/tasks/decision-detail-flow-clarity-pass/*`.
- 수정 금지:
  - `.env`
  - backend API contracts
  - DB migrations/schema
  - scheduler/timer 설정
  - broker/order execution logic

## Acceptance Criteria

- `/stocks/[symbol]` visible text does not expose `원장`, `문서 조각`, `검색 준비`, `RAG`, `artifact`, `LLM`, `Postgres`, `systemd`.
- `/recommendations/[id]` visible text avoids developer wording and clearly separates direct news, macro flow, score input, holding review, and paper-trade safety.
- `/paper-trading` clearly states actual broker submission count, paper candidate count, blocking reasons, and next page to inspect.
- EC2 route smoke passes for representative stock, recommendation, and paper-trading routes.

## Verification Commands

- verification command: `git diff --check`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-detail-flow-clarity-pass`
- verification command: EC2 route smoke for `/stocks/<symbol>`, `/recommendations/<id>`, `/paper-trading`
- verification command: Playwright snapshot for representative pages
