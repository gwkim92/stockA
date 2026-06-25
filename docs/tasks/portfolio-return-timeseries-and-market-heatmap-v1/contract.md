# portfolio-return-timeseries-and-market-heatmap-v1 Contract

## Task Request

- request: 기존 수집·분석 데이터로 화면 시각화를 더 풍성하게 만들고, 종목 전일 등락과 포트폴리오 수익률을 더 직관적으로 볼 수 있게 한다.
- context: `market-portfolio-return-visibility-v1`에서 전일 대비/평가손익률은 노출했지만, heatmap, 수익률 분포, 수집·분석 coverage matrix처럼 한눈에 보는 시각화가 부족하다.

## Goal

- goal: 기존 API DTO와 수집 결과를 그대로 사용해 `/stocks`, `/portfolio/coverage`, `/data-health`에 각각 종목 등락 heatmap, 포트폴리오 수익률 분포, 수집·분석 coverage matrix를 추가한다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/portfolio-return-timeseries-and-market-heatmap-v1/*`
  - `apps/web/src/app/stocks/*`
  - `apps/web/src/components/portfolio/*`
  - `apps/web/src/components/operations/*`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/lib/presentation/*`

## Invariants

- 추천 점수, 추천 순위, benchmark, portfolio position, broker/order flow를 변경하지 않는다.
- 데이터 수집 주기, provider selection, Toss promotion policy를 변경하지 않는다.
- 새 API endpoint, DB schema, scoring weight를 추가하지 않는다.
- 투자 판단 화면에 pipeline/run/artifact 같은 내부 용어를 새로 노출하지 않는다.

## Scope

- `/stocks`: 전일 대비 등락률 기반 heatmap을 추가한다.
- `/portfolio/coverage`: 평가손익률 분포를 막대형 시각화로 추가한다.
- `/data-health`: 가격, 뉴스, AI, 추천, 포트폴리오, 브로커 데이터의 수집·분석 coverage matrix를 추가한다.
- 각 시각화는 데이터 없음/미측정 상태를 명확히 표현한다.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-return-timeseries-and-market-heatmap-v1`
- verification command: `git diff --check`
- verification command: `Browser smoke for /stocks, /portfolio/coverage, /data-health`

## Acceptance Criteria

- `/stocks`는 상승·하락·보합·미측정 종목 분포를 heatmap으로 보여준다.
- `/portfolio/coverage`는 포지션별 수익률 분포를 막대형으로 보여준다.
- `/data-health`는 수집·분석 영역별 상태를 matrix로 보여준다.
- 375px, 768px, 1280px에서 가로 overflow가 없다.
- 기존 recommendation/scoring/portfolio/broker boundary는 변경되지 않는다.
