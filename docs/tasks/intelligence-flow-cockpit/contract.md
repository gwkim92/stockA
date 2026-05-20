# Task Contract

## Task

- 이름: intelligence-flow-cockpit
- 요청: 신호, 추천, 보유검토, 이벤트/AI 증거, 뉴스/공시 연관 추적이 사이트에서 한눈에 보이도록 정리한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/intelligence`에서 이벤트/공시, AI 증거, 테마/사이클, 추천, 투자 논리, 보유검토, 가상 거래 검증이 하나의 추적 흐름으로 보인다.
  - 사용자가 신호/추천/보유검토가 각각 어느 화면에 있는지 알 수 있다.
  - AI 분석은 추천 결론이 아니라 원천 문서와 구조화 증거로 표시된다.
  - 기존 read-only API contract를 유지한다.
  - broker write, 주문 제출, kill switch 해제, secret 출력은 하지 않는다.

## Scope

- `apps/web/src/app/intelligence/page.tsx` 신규 생성.
- `apps/web/src/app/layout.tsx` 내비게이션에 분석 지도 추가.
- `apps/web/src/app/page.tsx` 홈 CTA에 분석 지도 진입 링크 추가.
- `apps/web/src/app/globals.css`에 분석 지도 전용 레이아웃 스타일 추가.
- task plan/contract/handoff 갱신.

## Boundaries

- 추천 scoring formula, benchmark, schema, evaluation split을 바꾸지 않는다.
- 실시간 뉴스 provider 또는 신규 LLM 호출을 추가하지 않는다.
- 실제 broker API, 계좌 권한 변경, 주문 실행을 구현하지 않는다.
- API key, DB URL, read token, broker secret을 출력하지 않는다.
- 기존 이벤트/AI/추천 DTO shape를 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/plans/2026-05-19-intelligence-flow-cockpit.md`
  - `docs/tasks/intelligence-flow-cockpit/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/intelligence.html -w '%{http_code}' http://127.0.0.1:3001/intelligence`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task intelligence-flow-cockpit`
  - `git diff --check`

## Done Criteria

- [x] `/intelligence` route exists and renders from existing read-only API calls.
- [x] The page explains where signal/recommendation/holding review/AI evidence are visible.
- [x] Events are shown with linked AI evidence, source documents, theme, recommendation, thesis, and portfolio review context when available.
- [x] No new write endpoint, broker submit path, or secret exposure is introduced.
- [x] Required verification passes.
