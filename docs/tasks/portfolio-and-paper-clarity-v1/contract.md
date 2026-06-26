# portfolio-and-paper-clarity-v1 Contract

## Task Request

- request: 포트폴리오와 가상 거래 화면에서 수익률, 평단가, 차단 이유를 명확하게 보여준다.
- request: 현재 잔여 UX 정상화 범위에서 `/portfolio/coverage`와 `/paper-trading`의 큰 route 파일을 route-local 컴포넌트로 분해하고, 투자자 화면에서 내부 실행 용어보다 보유 수익률·차단 이유·실거래 경계를 먼저 보이게 한다.

## Goal

- goal: 한국인 개인 투자자가 `/portfolio/coverage`에서 보유 수량, 평단/원가, 평가손익, 수익률, 벤치마크 괴리, 리밸런싱 후보를 먼저 이해할 수 있게 한다.
- goal: 한국인 개인 투자자가 `/paper-trading`에서 가상 매매가 실제 주문인지, 안전장치로 차단됐는지, 데이터 부족인지, 승인이 필요한지 즉시 구분할 수 있게 한다.
- goal: route 파일은 데이터 조립과 섹션 composition 중심으로 축소하고, 세부 패널과 문구 변환은 route-local component/presentation helper로 이동한다.

## Scope

- `/portfolio/coverage`: quantity, average cost, market value, unrealized PnL, return percentage, benchmark state.
- `/paper-trading`: states are execution-ready, safety-blocked, data-limited, approval-required, live-trading-disabled.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/portfolio/coverage/_components/**`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/paper-trading/_components/**`
  - `apps/web/src/app/paper-trading/PaperTradingPage.module.css`
  - `apps/web/src/components/portfolio/**`
  - `apps/web/src/lib/presentation/**`
  - `docs/tasks/portfolio-and-paper-clarity-v1/**`

## Invariants

- No portfolio position mutation.
- No broker submit.
- No recommendation score change.
- No backend DTO change.
- No DB schema change.

## Verification Commands

- User can tell whether a position is profit/loss.
- User can tell why simulated trading is blocked or allowed.
- E2E route smoke for portfolio and paper trading.
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-and-paper-clarity-v1`
