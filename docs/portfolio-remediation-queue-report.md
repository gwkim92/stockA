# Portfolio Remediation Queue Report

이 문서는 portfolio review attention item을 다음 조치 단위로 분류하는 `portfolio-remediation-queue` 경로를 정의한다.

## Purpose

`portfolio-review-run-history`는 최근 review와 attention item을 보여준다. 운영 단계에서는 그 item이 thesis 보강 대상인지, outcome 생성 대상인지, position data 보정 대상인지 바로 구분되어야 한다.

`portfolio-remediation-queue`는 DB schema를 변경하지 않는 read-only CLI다. 최근 `portfolio.review_item` 중 조치가 필요한 action만 조회하고, deterministic rule로 `remediation_type`, `suggested_runner`, `suggested_next_step`을 붙여 JSON으로 출력한다. persistent 운영 상태가 필요하면 `portfolio-remediation-ticket-bootstrap`을 사용한다.

## Inputs

- required: `portfolio_name`
- optional:
  - `limit`
  - `review_source`
  - `action`
  - `remediation_type`

## Output

- `report_name`: `portfolio_remediation_queue`
- `portfolio_name`
- `limit`
- `review_source_filter`
- `action_filter`
- `remediation_type_filter`
- `queue_item_count`
- `remediation_type_counts`
- `action_counts`
- `items`

각 item은 review metadata, `symbol`, `action`, `remediation_type`, `suggested_runner`, `suggested_next_step`, `priority`, `risk_level`, `health_score`, `current_weight`, `recommended_weight`, `reason`을 포함한다.

## Remediation Mapping

- `needs_thesis_review`: `thesis_remediation`, `thesis_or_position_link_review`
- `needs_outcome_review`: `outcome_remediation`, `performance_outcome_runner`
- `needs_weight_review`: `position_data_remediation`, `portfolio_position_snapshot_upsert`
- `increase_to_target`: `allocation_review`, `allocation_policy_review`
- `trim_to_target`: `allocation_review`, `allocation_policy_review`
- `exit_review`: `risk_review`, `human_risk_review`
- `reduce_review`: `risk_review`, `human_risk_review`

## CLI

최근 5건:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-queue \
  --portfolio-name "Long Term Paper" \
  --limit 5
```

thesis 보강 대상만 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-queue \
  --portfolio-name "Long Term Paper" \
  --remediation-type thesis_remediation
```

특정 review action만 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-queue \
  --portfolio-name "Long Term Paper" \
  --action needs_thesis_review
```

## Verification

```bash
bash scripts/verify_portfolio_remediation_queue_report.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline을 실행한 뒤 coverage-gated portfolio review를 만든다. 이후 remediation queue JSON에서 아래를 확인한다.

- report name `portfolio_remediation_queue`
- portfolio name `Long Term Paper`
- queue item count `1`
- remediation type count `thesis_remediation: 1`
- action count `needs_thesis_review: 1`
- BABA queue item의 suggested runner `thesis_or_position_link_review`
- BABA reason에 `coverage status missing_thesis` 포함

## Boundaries

- DB schema를 변경하지 않는다.
- review action rule을 변경하지 않는다.
- queue state를 저장하지 않는다.
- remediation을 자동 실행하지 않는다.
- 실거래 주문/체결과 무관하다.
- LLM 판단은 아직 범위 밖이다.

## Next Steps

- daily automation으로 run history, remediation queue, remediation ticket bootstrap을 같이 실행한다.
- `portfolio-remediation-ticket-report`로 open ticket 운영 리포트를 추가한다.
- thesis remediation은 active thesis 생성 또는 position-thesis link 보정 runner로 연결한다.
