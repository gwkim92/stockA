# Session Handoff

## Active Task

- 이름: frontend-korean-localization-and-positive-budget-run
- 담당: Codex
- 날짜: 2026-05-17

## Current Status

- 완료:
  - positive-budget Alpha Vantage run result recorded.
  - Korean label helper added.
  - major Next.js cockpit pages localized.
  - local live route smoke passed.
- 진행 중:
  - none.
- 막힌 점:
  - MSFT/NVDA 가격을 실제로 적재하려면 먼저 market universe canonical instrument bootstrap이 필요하다.

## Positive Budget Run

- 실행일: 2026-05-17
- watchlist: `MSFT`, `NVDA`, `AAPL`
- free provider budget used for the positive smoke: `daily_budget=1`, `max_requests_per_run=1`
- 결과: provider request 1회를 사용했지만 `MSFT`가 canonical instrument 미등록으로 실패했다.
- ledger 결과 at that moment: used request count가 1로 증가했고 conservative smoke budget 기준 remaining request count는 0이었다.
- 이후 2026-05-17 local live runtime에서 공식 Alpha Vantage free-tier cap assumption인 `25/day`로 ledger를 provider call 없이 정정했다. 현재 local ledger는 `used=1`, `remaining=24`다.
- `NVDA`, `AAPL`은 해당 smoke의 request budget 소진으로 실행되지 않았다.

## Implemented

- Next.js cockpit 주요 화면의 정적 문구를 한국어로 전환했다.
- `apps/web/src/lib/korean-labels.ts`를 추가해 status/action/risk/code/reason 표시를 한국어로 매핑했다.
- dashboard, data-health, remediation, cycles, events, recommendation detail, thesis detail, theme detail, AI evidence, source document, portfolio coverage, performance, loading/error/not-found 문구를 갱신했다.
- local live `/data-health`에서 무료 provider budget은 현재 `24/25`, `1회 사용`으로 표시된다.

## Verification

- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-home.html -w "%{http_code}\n" http://127.0.0.1:3001/`
- `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-data-health.html -w "%{http_code}\n" http://127.0.0.1:3001/data-health`
- `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-remediation.html -w "%{http_code}\n" http://127.0.0.1:3001/remediation`
- `curl -sS -o /private/tmp/stockanalysis-runtime/smoke-performance.html -w "%{http_code}\n" http://127.0.0.1:3001/performance`
- `rg` smoke checked that the known old English phrases no longer appear in the rendered local HTML.
- `git diff --check`

## Exact Next Step

- exact next step: market universe bootstrap으로 MSFT/NVDA canonical instrument를 등록한다.
- 이후 Alpha Vantage는 소형 우선순위 watchlist fallback으로만 쓰고, broad universe용 무료/저비용 market data provider를 별도 pilot한다.
- backend 자유문장 생성부 자체를 한국어로 저장할지, UI에서 계속 표시 매핑할지 결정한다.
