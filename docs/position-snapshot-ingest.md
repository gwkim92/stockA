# Position Snapshot Ingest

이 문서는 표준 CSV position snapshot을 canonical portfolio tables에 업서트하는 경로를 설명한다.

## Goal

- source:
  - CSV file
- target:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`

이 단계의 목적은 portfolio review를 위해 position snapshot을 수동 SQL 삽입이 아니라 수집기/업서터로 저장하는 것이다.

## CSV Schema

필수 컬럼:

- `symbol`
- `quantity`
- `market_price`
- `market_value`

선택 컬럼:

- `cost_basis`
- `weight`
- `unrealized_pnl`
- `linked_thesis_id`

현재 fixture 예시는 `tests/fixtures/portfolio_positions_long_term_paper.csv`다.

```csv
symbol,quantity,cost_basis,market_price,market_value,weight,unrealized_pnl,linked_thesis_id
AAPL,10.00000000,210.910000,222.910000,2229.10,0.0500,120.00,
```

`linked_thesis_id`가 비어 있으면 해당 instrument의 latest active thesis를 자동 연결한다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-position-snapshot-upsert \
  --positions-csv tests/fixtures/portfolio_positions_long_term_paper.csv \
  --portfolio-name "Long Term Paper" \
  --snapshot-date 2024-11-01 \
  --strategy-name long_term_core
```

기본값:

- `--base-currency USD`
- `--market-code US`
- paper portfolio 기본값 true

`--live`를 넘기면 portfolio row의 `is_paper`가 false로 저장된다. 단, 이것은 실계좌 sync가 아니라 CSV row의 성격을 표시하는 플래그일 뿐이다.

## Boundary

- broker API 또는 실계좌 sync는 아직 없다.
- 주문, 거래, 리밸런싱은 생성하지 않는다.
- CSV는 canonical symbol 기준이다.
- cash position row는 아직 별도로 적재하지 않는다.
- 복수 active thesis가 있으면 latest `thesis_id`를 사용한다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_position_snapshot_ingest.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task position-snapshot-ingest`

현재 Docker verify는 아래를 이어 실행한다.

```text
market-universe-bootstrap
-> market-price-universe-backfill
-> strategy-universe-slice
-> market-feature-snapshot
-> sec-filings-upsert
-> sec-filing-raw-fetch
-> sec-filings-event-extract
-> event-classification-impact-bootstrap
-> event-instrument-impact-bootstrap
-> instrument-theme-enrichment
-> cycle-state-snapshot
-> recommendation-bootstrap
-> thesis-bootstrap
-> thesis-review-bootstrap
-> portfolio-position-snapshot-upsert
-> portfolio-review-bootstrap
```

그리고 paper portfolio 1건, AAPL position snapshot 1건, linked active thesis 1건, latest `portfolio_position_snapshot_upsert` pipeline run status 성공, downstream portfolio review item action `monitor`를 확인한다.

## Next Step

1. `performance-outcome-bootstrap`
2. `portfolio-weight-distribution-report`
3. broker-specific position adapter
