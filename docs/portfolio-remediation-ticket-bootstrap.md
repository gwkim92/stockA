# Portfolio Remediation Ticket Bootstrap

이 문서는 portfolio review remediation queue item을 persistent 운영 ticket으로 저장하는 `portfolio-remediation-ticket-bootstrap` 경로를 정의한다.

## Purpose

`portfolio-remediation-queue`는 read-only report다. 현재 조치 후보를 보여주지만, 운영 상태를 저장하지 않는다.

`portfolio-remediation-ticket-bootstrap`은 같은 queue 후보를 `portfolio.remediation_ticket`에 upsert한다. 이 table은 어떤 remediation이 열려 있는지, 어떤 runner가 제안됐는지, 마지막으로 언제 다시 관측됐는지 추적하기 위한 최소 persistent queue다.

## Schema

`portfolio.remediation_ticket`은 아래 identity로 중복을 막는다.

```text
(portfolio_review_id, instrument_id, action, remediation_type)
```

핵심 필드:

- `status`: `open`, `in_progress`, `resolved`, `ignored`
- `remediation_type`
- `suggested_runner`
- `suggested_next_step`
- `latest_reason`
- `source_run_id`
- `opened_at`
- `updated_at`
- `last_seen_at`
- `resolved_at`

`portfolio.review_item`은 review rerun 때 delete/insert되므로 ticket은 `review_item_id` FK를 갖지 않는다.

## CLI

최근 review queue item을 ticket으로 저장:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-bootstrap \
  --portfolio-name "Long Term Paper" \
  --limit 5
```

thesis remediation만 저장:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-bootstrap \
  --portfolio-name "Long Term Paper" \
  --remediation-type thesis_remediation
```

특정 action만 저장:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-bootstrap \
  --portfolio-name "Long Term Paper" \
  --action needs_thesis_review
```

## Output

- `report_name`: `portfolio_remediation_ticket_bootstrap`
- `run_id`
- `portfolio_name`
- `ticket_count`
- `remediation_type_counts`
- `action_counts`
- `tickets`

각 ticket은 `symbol`, `action`, `remediation_type`, `suggested_runner`, `suggested_next_step`, `status`, `priority`, `risk_level`, `health_score`, `current_weight`, `recommended_weight`, `reason`을 포함한다.

## Verification

```bash
bash scripts/verify_portfolio_remediation_ticket_bootstrap.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline을 실행한 뒤 coverage-gated portfolio review를 만든다. 이후 ticket bootstrap을 두 번 실행해 아래를 확인한다.

- BABA `needs_thesis_review` ticket 1건 생성
- ticket status `open`
- remediation type `thesis_remediation`
- suggested runner `thesis_or_position_link_review`
- reason에 `coverage status missing_thesis` 포함
- bootstrap 2회 실행 후 DB ticket count가 여전히 `1`
- `portfolio_remediation_ticket_bootstrap` pipeline run 2건이 `succeeded`

## Boundaries

- remediation을 자동 실행하지 않는다.
- 실거래 주문/체결과 무관하다.
- review action rule을 변경하지 않는다.
- recommendation, thesis, attribution, performance outcome 산식을 변경하지 않는다.
- ticket resolve/ignore command는 아직 없다.

## Next Steps

- `resolved`/`ignored` lifecycle command를 추가한다.
- thesis remediation runner를 별도 설계해 active thesis 생성 또는 position-thesis link 보정을 처리한다.
