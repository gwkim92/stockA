# Performance Outcome Bootstrap

이 문서는 추천과 투자 thesis의 사후 성과를 저장하는 첫 performance 경로를 고정한다.

## Purpose

`performance-outcome-bootstrap`은 이미 생성된 recommendation batch를 기준으로 특정 측정 종료일의 가격 성과를 계산해 `performance.recommendation_outcome`과 `performance.thesis_outcome`에 저장한다. `performance-outcome-batch-bootstrap`은 같은 계산을 여러 measurement date에 대해 순차 실행한다.

이 단계는 추천 또는 보유 판단을 바꾸지 않는다. 역할은 사후 검증이다. 즉, 당시 추천, thesis, 가격 데이터가 이후 어떤 결과를 냈는지 저장해 추천 품질과 thesis 품질을 추적한다.

due horizon 자동 실행은 `docs/scheduled-outcome-runner.md`의 `performance-outcome-schedule-bootstrap`이 담당한다.

## Inputs

- recommendation identity: `as_of_date`, `market_code`, `strategy_name`, `horizon_type`, `universe_version`
- measurement identity: `measurement_end_date`, `outcome_version`
- source tables:
  - `signal.recommendation_batch`
  - `signal.recommendation`
  - `signal.investment_thesis`
  - `market.daily_price_bar`

## Price Rules

- entry price: recommendation batch `as_of_date` 이하 최신 `adjusted_close`
- exit price: `measurement_end_date` 이하, entry date 이상 최신 `adjusted_close`
- max drawdown: entry date부터 exit date까지의 최저 `adjusted_close` 기준
- benchmark: thesis `benchmark_code`와 같은 `ref.instrument.primary_symbol`이 있고 benchmark price가 있으면 계산한다.
- benchmark가 없으면 `benchmark_return_pct`, `alpha_pct`는 null로 둔다.

## Formula

- absolute return: `(exit_price - entry_price) / entry_price`
- benchmark return: `(benchmark_exit_price - benchmark_entry_price) / benchmark_entry_price`
- alpha: `absolute_return_pct - benchmark_return_pct`
- max drawdown: `(min_price - entry_price) / entry_price`

모든 return 계열 값은 소수점 6자리로 quantize한다.

## Labels

- benchmark가 있으면 alpha 기준:
  - `outperform`: alpha > 0
  - `underperform`: alpha < 0
  - `inline`: alpha = 0
- benchmark가 없으면 absolute return 기준:
  - `positive`: return > 0
  - `negative`: return < 0
  - `flat`: return = 0

thesis outcome은 recommendation outcome label을 사후 검토 상태로 변환한다.

- `working`: positive 또는 outperform
- `challenged`: negative 또는 underperform
- `neutral`: flat 또는 inline

## CLI

단일 측정일:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-bootstrap \
  --as-of-date 2024-11-01 \
  --measurement-end-date 2024-11-04 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1
```

여러 측정일 또는 horizon day:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-batch-bootstrap \
  --as-of-date 2024-11-01 \
  --measurement-end-date 2024-11-04 \
  --horizon-day 31 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1
```

`--horizon-day`는 calendar day 기준으로 `as_of_date + n days`를 measurement date로 만든다. 실제 거래일 보정은 price lookup의 latest-on-or-before rule에 맡긴다.

due horizon schedule:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli performance-outcome-schedule-bootstrap \
  --due-on-date 2024-12-02 \
  --horizon-day 3 \
  --horizon-day 31 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --outcome-version bootstrap-v1
```

schedule runner는 outcome이 비어 있는 due batch/horizon만 찾아 기존 단일 outcome runner를 호출한다.

## Verification

```bash
bash scripts/verify_performance_outcome_bootstrap.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, 데이터 수집기 기반 AAPL/SPY 가격 upsert와 recommendation/thesis 생성 후 AAPL outcome 2건을 확인한다.

기대값:

- `performance.recommendation_outcome` 2건
- `performance.thesis_outcome` 2건
- 2024-11-04 AAPL `absolute_return_pct = 0.010000`
- 2024-11-04 SPY `benchmark_return_pct = 0.005000`
- 2024-11-04 AAPL `alpha_pct = 0.005000`
- 2024-12-02 AAPL `absolute_return_pct = 0.100000`
- 2024-12-02 SPY `benchmark_return_pct = 0.040000`
- 2024-12-02 AAPL `alpha_pct = 0.060000`
- AAPL recommendation outcome labels `outperform`
- AAPL thesis outcome success grade `pass`
- latest `performance_outcome_bootstrap` pipeline run status `succeeded`

## Boundaries

- 실거래 PnL은 계산하지 않는다.
- 이 경로 자체는 portfolio-level attribution을 계산하지 않는다. portfolio attribution은 `docs/portfolio-attribution-bootstrap.md`의 별도 runner가 담당한다.
- 이 경로 자체는 sector/theme attribution을 계산하지 않는다.
- AI grading은 넣지 않는다.
- 현재 fixture는 3일과 31일 horizon 검증이다. 실제 중장기/장기 검증은 더 긴 가격 history가 붙은 뒤 별도 확장한다.

## Next Steps

- attribution coverage report를 추가해 outcome 없는 position을 별도로 추적한다.
- 실제 cron/heartbeat automation에서 schedule runner를 호출한다.
