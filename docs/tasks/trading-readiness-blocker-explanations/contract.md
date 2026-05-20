# Task Contract

## Task

- 이름: trading-readiness-blocker-explanations
- 요청: 거래 안전 화면에서 가상 검증 실패 사유를 사람이 이해할 수 있는 한국어 설명과 다음 조치로 보여준다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `paper_validation.blocked_reasons`가 화면에 표시된다.
  - `AAPL:single_order_notional_limit_exceeded` 같은 내부 reason code가 한국어 원인/다음 조치로 풀린다.
  - 화면은 여전히 read-only이며 주문 버튼, broker write endpoint, kill switch unlock을 제공하지 않는다.
  - broker secret, account credential, OAuth token, DB URL, read token을 출력하지 않는다.

## Scope

- `apps/web/src/lib/korean-labels.ts`에 blocked reason 해석 helper 추가.
- `apps/web/src/app/trading-readiness/page.tsx`에 차단 사유 목록 추가.
- `apps/web/src/app/globals.css`에 reason list 스타일 추가.
- task docs와 verification 갱신.

## Boundaries

- broker API를 호출하지 않는다.
- 실제 주문, fill, execution report, P&L 반영은 하지 않는다.
- kill switch를 해제하지 않는다.
- FastAPI write endpoint를 만들지 않는다.
- 추천 scoring, benchmark, evaluation split은 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/plans/2026-05-19-trading-readiness-blocker-explanations.md`
  - `docs/tasks/trading-readiness-blocker-explanations/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_trading_paper_validation tests.test_trading_safety`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task trading-readiness-blocker-explanations`
  - `git diff --check`

## Done Criteria

- [x] blocked reasons render in Korean on `/trading-readiness`.
- [x] broker 제출 remains visible as 0건.
- [x] no secret values are introduced.
- [x] Next typecheck/build pass.
- [x] required verification passes.
