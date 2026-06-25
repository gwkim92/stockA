# market-portfolio-return-visibility-v1 Contract

## Task Request

- request: 종목들의 전일 대비 증가·감소율과 포트폴리오 수익률을 화면에 명확히 표시하고, 수집·분석 데이터 중 화면 누락 영역과 시각화 보강 가능성을 점검한다.
- context: `/api/stocks`는 `latest_price.change_pct`를 제공하고, `/api/portfolio/.../coverage`는 position별 평가액·원가·평가손익 필드를 제공하지만 투자 판단 화면에서 수익률이 충분히 보이지 않는다.

## Goal

- goal: 기존 수집/분석/포트폴리오 DTO를 변경하지 않고 프론트 presentation 계층에서 전일 대비 등락률, 포트폴리오 총 평가손익률, 종목별 평가손익률을 사용자용 한국어 UI로 노출한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/market-portfolio-return-visibility-v1/*`
  - `apps/web/src/lib/presentation/*`
  - `apps/web/src/components/research/*`
  - `apps/web/src/components/portfolio/*`
  - `apps/web/src/app/stocks/*`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/app/globals.css`
  - `src/stockanalysis/frontend/live_adapter.py`

## Invariants

- 추천 점수, 추천 순위, benchmark, portfolio position, broker/order flow를 변경하지 않는다.
- Toss/글로벌 가격 수집 정책과 provider promotion policy를 변경하지 않는다.
- 실거래 주문과 자동 weight 변경은 계속 닫아둔다.
- 화면 변경은 기존 API DTO의 읽기/표현 계층에 한정한다.

## Scope

- 종목 목록과 종목 상세에 전일 대비 등락률을 사용자용 한국어 문구와 시각 상태로 표시한다.
- 포트폴리오 화면에 총 평가금액, 총 평가손익, 총 수익률, 종목별 손익률을 표시한다.
- 기존 수집/분석 데이터 중 화면에서 빠진 영역과 시각화 보강 여지를 보고한다.

## Non-goals

- 추천 점수, 추천 순위, portfolio position, benchmark, broker/order flow를 변경하지 않는다.
- 새 데이터 수집 provider를 추가하지 않는다.
- 실거래 주문 또는 weight 변경을 열지 않는다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-portfolio-return-visibility-v1`
- verification command: `git diff --check`
- verification command: `Browser smoke for /stocks, /stocks/AAPL, /portfolio/coverage`

## Acceptance Criteria

- `/stocks`와 `/stocks/[symbol]`에서 전일 대비 등락률이 상승·하락·보합·미측정 상태로 구분된다.
- `/portfolio/coverage`에서 총 평가액, 원가, 평가손익, 평가손익률, position별 평가손익률이 보인다.
- 내부 운영 용어를 투자 판단 영역에 추가로 노출하지 않는다.
- 기존 추천/scoring/portfolio/broker boundary는 변경되지 않는다.
