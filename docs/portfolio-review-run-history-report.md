# Portfolio Review Run History Report

이 문서는 최근 portfolio review 실행 상태와 조치 후보를 조회하는 `portfolio-review-run-history` 경로를 정의한다.

## Purpose

`portfolio-review-bootstrap`과 coverage gate는 review 결과를 `portfolio.review`, `portfolio.review_item`에 저장한다. 하지만 운영 관점에서는 최근 review가 성공했는지, risk가 무엇인지, 어떤 position이 조치 대상인지 바로 확인할 수 있어야 한다.

`portfolio-review-run-history`는 DB schema를 변경하지 않는 read-only CLI다. 최근 review runs를 조회하고 risk/action 집계와 attention items를 JSON으로 출력한다.

## Inputs

- required: `portfolio_name`
- optional:
  - `limit`
  - `review_source`
  - `risk_level`
  - `action`

## Output

- `report_name`: `portfolio_review_run_history`
- `portfolio_name`
- `review_count`
- `risk_counts`
- `action_counts`
- `attention_item_count`
- `latest_review`
- `reviews`

각 `reviews` 항목은 review header, source run status, item count, action counts, attention items를 포함한다.

`attention_items`는 아래 action을 가진 item만 포함한다.

- `exit_review`
- `reduce_review`
- `needs_thesis_review`
- `needs_outcome_review`
- `needs_weight_review`
- `increase_to_target`
- `trim_to_target`

## CLI

최근 5건:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-review-run-history \
  --portfolio-name "Long Term Paper" \
  --limit 5
```

특정 action을 포함한 review만 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-review-run-history \
  --portfolio-name "Long Term Paper" \
  --action needs_thesis_review
```

## Verification

```bash
bash scripts/verify_portfolio_review_run_history_report.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline을 실행한 뒤 coverage-gated portfolio review를 만든다. 이후 report JSON에서 아래를 확인한다.

- review count `1`
- risk count `watch: 1`
- action count `monitor: 1`
- action count `needs_thesis_review: 1`
- attention item count `1`
- latest review item count `2`
- BABA attention item action `needs_thesis_review`
- BABA reason에 `coverage status missing_thesis` 포함

## Boundaries

- DB schema를 변경하지 않는다.
- portfolio review action rule을 변경하지 않는다.
- remediation을 자동 실행하지 않는다.
- LLM report generation은 아직 범위 밖이다.

## Next Steps

- 이 report를 cron/automation으로 실행해 daily 운영 스냅샷을 남긴다.
- `portfolio-remediation-queue`로 attention item을 remediation type과 suggested runner로 분류한다.
- dashboard가 생기면 latest review와 attention items를 첫 화면에 노출한다.
