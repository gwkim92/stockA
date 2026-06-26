# portfolio-and-paper-clarity-v1 Contract

## Request

- 포트폴리오와 가상 거래 화면에서 수익률, 평단가, 차단 이유를 명확하게 보여준다.

## Scope

- `/portfolio/coverage`: quantity, average cost, market value, unrealized PnL, return percentage, benchmark state.
- `/paper-trading`: states are execution-ready, safety-blocked, data-limited, approval-required, live-trading-disabled.

## Invariants

- No portfolio position mutation.
- No broker submit.
- No recommendation score change.

## Verification

- User can tell whether a position is profit/loss.
- User can tell why simulated trading is blocked or allowed.
- E2E route smoke for portfolio and paper trading.
