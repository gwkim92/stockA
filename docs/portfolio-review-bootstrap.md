# Portfolio Review Bootstrap

이 문서는 현재 position snapshot을 recommendation, thesis, thesis review evidence와 연결해 포트폴리오 보유 검토 결과를 저장하는 경로를 설명한다.

## Goal

- source:
  - `portfolio.portfolio`
  - `portfolio.position_snapshot`
  - `signal.recommendation_batch`
  - `signal.recommendation`
  - `signal.investment_thesis`
  - `signal.thesis_review`
- target:
  - `portfolio.review`
  - `portfolio.review_item`

이 단계의 목적은 "추천했다"에서 멈추지 않고, 실제 보유 중인 position을 계속 보유해도 되는지 검토한 기록을 남기는 것이다.

## Current Action Rule

portfolio action은 deterministic rule로 만든다.

- optional coverage gate가 켜져 있고 coverage status가 `missing_thesis`이면 `needs_thesis_review`
- optional coverage gate가 켜져 있고 coverage status가 `missing_outcome`이면 `needs_outcome_review`
- optional coverage gate가 켜져 있고 coverage status가 `missing_weight`이면 `needs_weight_review`
- thesis review action `exit` -> `exit_review`
- thesis review action `reduce` -> `reduce_review`
- thesis review action `watch` -> `monitor`
- linked thesis와 recommendation이 모두 없으면 `needs_thesis_review`
- thesis review가 `keep`이고 current weight가 recommended weight의 75%보다 낮으면 `increase_to_target`
- thesis review가 `keep`이고 current weight가 recommended weight의 125%보다 높으면 `trim_to_target`
- 그 외에는 `hold`

현재 fixture chain에서는 AAPL position snapshot 1건이 아래처럼 저장된다.

```text
portfolio: Long Term Paper
symbol: AAPL
current_weight: 0.0500
thesis_review_action: watch
thesis_health_score: 0.3610
portfolio_review_item.action: monitor
portfolio_review.risk_level: watch
portfolio_review.cash_weight: 0.9500
```

coverage gate는 선택 옵션이다. 아래처럼 measurement end date를 넘기면 position-linked thesis 기준으로 `performance.thesis_outcome`을 확인하고, coverage status를 review reason과 summary에 포함한다.

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-review-bootstrap \
  --portfolio-name "Long Term Paper" \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --coverage-measurement-end-date 2024-12-02
```

coverage gate fixture에서는 AAPL이 `covered` 상태로 `monitor`를 유지하고, BABA는 position-linked thesis가 없어 `needs_thesis_review`로 저장된다.

## Boundary

- portfolio review는 주문이나 거래를 생성하지 않는다.
- broker, 실계좌, 실거래 연동은 범위 밖이다.
- AI는 portfolio action을 직접 결정하지 않는다.
- 현재는 paper portfolio와 snapshot rows를 입력으로 사용한다.
- coverage gate는 missing thesis/outcome/weight를 자동 보정하지 않는다.
- coverage gate는 position-linked thesis 기준이다. recommendation에 thesis가 있어도 position snapshot에 thesis가 없으면 보유 thesis 연결이 빠진 것으로 본다.

## Verification

- `bash /Users/woody/ai/stockanalysis/scripts/verify_portfolio_review_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-bootstrap`

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
-> performance-outcome-batch-bootstrap
-> portfolio-position-snapshot-upsert
-> portfolio-review-bootstrap --coverage-measurement-end-date
```

그리고 CSV 기반 position snapshot이 저장된 뒤 `portfolio.review` table 존재, `portfolio.review_item` table 존재, review header 1건, review item 1건, AAPL action `monitor`, health score `0.3610`, current weight `0.0500`, latest `portfolio_review_bootstrap` pipeline run status 성공을 확인한다. 이후 coverage gate 시나리오에서 AAPL `monitor` with `covered`, BABA `needs_thesis_review` with `missing_thesis`, review item 2건, latest run status 성공을 확인한다.

최근 review run과 attention items 조회는 `docs/portfolio-review-run-history-report.md`의 `portfolio-review-run-history`가 담당한다.

## Next Step

1. portfolio review 운영 스케줄러
2. remediation queue
3. review/coverage dashboard
