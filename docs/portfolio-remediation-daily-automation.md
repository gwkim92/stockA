# Portfolio Remediation Daily Automation

이 문서는 daily portfolio review 운영 순서를 하나로 묶는 `portfolio-remediation-daily-run` 경로를 정의한다.

## Purpose

기존 운영 경로는 아래처럼 분리되어 있다.

1. `portfolio-review-bootstrap`
2. `portfolio-remediation-ticket-bootstrap`
3. `portfolio-remediation-ticket-report`

`portfolio-remediation-daily-run`은 이 세 단계를 같은 입력으로 순서대로 실행한다. 새 판단 로직을 만들지 않고, 검증된 deterministic runner를 조합해 반복 운영 실수를 줄이는 것이 목적이다.

## Run Order

1. portfolio review를 저장한다.
2. review attention item을 persistent remediation ticket으로 upsert한다.
3. ticket backlog report를 출력한다.

Ticket status update는 자동으로 실행하지 않는다. 운영자는 report를 확인한 뒤 필요할 때 `portfolio-remediation-ticket-update`로 `in_progress`, `resolved`, `ignored`를 명시적으로 기록한다.

## CLI

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-daily-run \
  --portfolio-name "Long Term Paper" \
  --as-of-date 2024-11-01 \
  --strategy-name long_term_core \
  --horizon-type long_term \
  --universe-version fixture-v1 \
  --coverage-measurement-end-date 2024-12-02 \
  --ticket-limit 20 \
  --ticket-status open
```

## Output

- `report_name`: `portfolio_remediation_daily_automation`
- `run_id`: top-level automation pipeline run id
- `portfolio_name`
- `as_of_date`
- `strategy_name`
- `horizon_type`
- `universe_version`
- `coverage_measurement_end_date`
- `ticket_limit`
- `ticket_status_filter`
- `steps`
- `review`
- `ticket_bootstrap`
- `ticket_report`

`steps`는 실행 순서를 고정한다. `review`, `ticket_bootstrap`, `ticket_report`는 각 하위 runner의 원본 summary다.

## Verification

```bash
bash scripts/verify_portfolio_remediation_daily_automation.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position prerequisite pipeline을 만든다. 이후 `portfolio-remediation-daily-run`을 실행해 아래를 확인한다.

- daily report name `portfolio_remediation_daily_automation`
- step order `portfolio_review_bootstrap -> portfolio_remediation_ticket_bootstrap -> portfolio_remediation_ticket_report`
- coverage-gated review item 2건
- BABA open ticket 1건
- remediation type `thesis_remediation`
- suggested runner `thesis_or_position_link_review`
- top-level `portfolio_remediation_daily_automation` pipeline run status `succeeded`

## Boundaries

- 실제 OS cron, hosted automation, app automation은 활성화하지 않는다.
- DB schema를 변경하지 않는다.
- ticket을 자동으로 resolved/ignored 처리하지 않는다.
- remediation을 자동 실행하지 않는다.
- 실거래 주문/체결과 무관하다.
- review action rule, recommendation, thesis, attribution, performance outcome 산식을 변경하지 않는다.
- LLM 호출을 추가하지 않는다.

## Next Steps

- scheduler activation 전 정책은 `docs/portfolio-remediation-scheduler-contract.md`에 정의한다.
- open ticket oldest age와 status counts를 dashboard 첫 화면에 노출한다.
- assignee/note/due date가 필요하면 ticket schema extension을 별도 작업으로 진행한다.
