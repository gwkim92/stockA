# Portfolio Remediation Ticket Report

이 문서는 persistent remediation ticket을 조회하는 `portfolio-remediation-ticket-report` 경로를 정의한다.

## Purpose

`portfolio-remediation-ticket-bootstrap`은 조치 필요 항목을 `portfolio.remediation_ticket`에 저장한다. 운영자는 이 ticket을 상태별로 조회해 어떤 remediation이 아직 열려 있는지 확인해야 한다.

`portfolio-remediation-ticket-report`는 DB schema를 변경하지 않는 read-only CLI다. ticket, review, portfolio, instrument, pipeline metadata를 join해 운영 리포트 JSON을 출력한다.

## Inputs

- required: `portfolio_name`
- optional:
  - `limit`
  - `status`
  - `action`
  - `remediation_type`
  - `suggested_runner`

기본 `status`는 `open`이다. 모든 상태를 조회하려면 `--status all`을 사용한다.

## Output

- `report_name`: `portfolio_remediation_ticket_report`
- `portfolio_name`
- `limit`
- `status_filter`
- `action_filter`
- `remediation_type_filter`
- `suggested_runner_filter`
- `ticket_count`
- `status_counts`
- `remediation_type_counts`
- `action_counts`
- `tickets`

각 ticket은 review metadata, `instrument_id`, `symbol`, `action`, `remediation_type`, `suggested_runner`, `suggested_next_step`, `status`, priority/score/weight fields, `reason`, `source_run_status`, `opened_at`, `updated_at`, `last_seen_at`, `resolved_at`을 포함한다.

## CLI

open ticket 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-report \
  --portfolio-name "Long Term Paper" \
  --limit 20
```

모든 상태 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-report \
  --portfolio-name "Long Term Paper" \
  --status all
```

thesis remediation만 조회:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-report \
  --portfolio-name "Long Term Paper" \
  --status open \
  --remediation-type thesis_remediation
```

## Verification

```bash
bash scripts/verify_portfolio_remediation_ticket_report.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline을 실행한 뒤 coverage-gated portfolio review와 remediation ticket bootstrap을 만든다. 이후 ticket report JSON에서 아래를 확인한다.

- report name `portfolio_remediation_ticket_report`
- portfolio name `Long Term Paper`
- ticket count `1`
- status filter `open`
- remediation type filter `thesis_remediation`
- status count `open: 1`
- action count `needs_thesis_review: 1`
- BABA ticket status `open`
- BABA suggested runner `thesis_or_position_link_review`
- source run status `succeeded`
- reason에 `coverage status missing_thesis` 포함

## Boundaries

- DB schema를 변경하지 않는다.
- ticket 상태를 변경하지 않는다.
- remediation을 자동 실행하지 않는다.
- 실거래 주문/체결과 무관하다.
- review action rule, recommendation, thesis, attribution, performance outcome 산식을 변경하지 않는다.

## Next Steps

- daily automation으로 ticket report를 생성해 open remediation backlog를 추적한다.
- dashboard가 생기면 open ticket count와 oldest open ticket을 첫 화면에 노출한다.
- frontend live read adapter가 이 report를 `RemediationTicketsResponse` DTO로 변환한다.
