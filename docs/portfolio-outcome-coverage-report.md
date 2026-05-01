# Portfolio Outcome Coverage Report

이 문서는 `portfolio-outcome-coverage-report`의 역할과 경계를 고정한다.

## Purpose

`portfolio-attribution-bootstrap`은 보유 snapshot과 thesis outcome이 모두 연결된 position만 attribution component로 저장한다. 이 방식은 설명 가능한 attribution을 만들기에는 안전하지만, thesis나 outcome이 빠진 position이 조용히 제외될 수 있다.

`portfolio-outcome-coverage-report`는 이 blind spot을 별도로 드러내는 read-only CLI다. portfolio snapshot 전체를 기준으로 position별 coverage status, count, weight, cash weight, coverage ratio를 JSON으로 출력한다.

## Coverage Status

- `covered`: position에 linked thesis가 있고, 해당 thesis의 requested measurement outcome도 존재한다.
- `missing_thesis`: position에 linked thesis가 없다. 현재 attribution 대상이 될 수 없다.
- `missing_outcome`: linked thesis는 있지만 requested measurement outcome이 없다. outcome runner를 추가 실행해야 한다.
- `missing_weight`: position weight가 없다. count 기준으로는 식별되지만 weight coverage와 cash weight 해석이 제한된다.

## Inputs

- portfolio identity: `portfolio_name`
- snapshot identity: `snapshot_date`
- outcome identity: `measurement_end_date`
- source tables:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`
  - `ref.instrument`
  - `signal.investment_thesis`
  - `performance.thesis_outcome`

## Output

CLI는 JSON summary를 stdout으로 출력한다.

- `position_count`: snapshot 내 non-zero position 수
- `status_counts`: status별 position count
- `weight_by_status`: status별 position weight 합계
- `total_position_weight`: known position weight 합계
- `covered_weight`: attribution 가능한 position weight 합계
- `cash_weight`: `1 - total_position_weight`; weight 누락이 있으면 `null`
- `coverage_ratio_by_count`: covered count / position count
- `coverage_ratio_by_weight`: covered weight / known position weight
- `positions`: position별 status와 thesis/outcome metadata

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-outcome-coverage-report \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --measurement-end-date 2024-12-02
```

## Verification

```bash
bash scripts/verify_portfolio_outcome_coverage_report.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/outcome/position pipeline을 실행한 뒤 coverage report JSON을 확인한다.

기대값:

- position count `2`
- AAPL `covered`
- BABA `missing_thesis`
- covered count `1`
- missing thesis count `1`
- covered weight `0.0500`
- missing thesis weight `0.0300`
- total position weight `0.0800`
- cash weight `0.9200`
- count coverage ratio `0.5000`
- weight coverage ratio `0.6250`

## Boundaries

- DB schema를 변경하지 않는다.
- attribution methodology를 변경하지 않는다.
- missing thesis나 missing outcome을 자동 생성하지 않는다.
- 실거래 PnL을 계산하지 않는다.
- LLM 판단을 사용하지 않는다. 이후 report generation에서 결과 해석 문장을 생성할 수는 있지만, coverage status 자체는 DB state에서 결정한다.

## Next Steps

- scheduled outcome runner와 연결해 `missing_outcome`을 줄이는 운영 리포트를 만든다.
- portfolio review coverage gate는 `portfolio-review-bootstrap --coverage-measurement-end-date`로 추가되었다.
- dashboard가 생기면 attribution result와 coverage report를 같은 화면에서 확인하게 한다.
