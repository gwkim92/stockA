# Portfolio Remediation Ticket Update

이 문서는 persistent remediation ticket의 lifecycle status를 변경하는 `portfolio-remediation-ticket-update` 경로를 정의한다.

## Purpose

`portfolio-remediation-ticket-report`는 backlog를 보여준다. 운영 루프를 닫으려면 ticket을 처리 시작, 해결, 무시 상태로 변경하는 명시적 경로가 필요하다.

`portfolio-remediation-ticket-update`는 특정 portfolio의 ticket 1건만 찾아 status를 변경한다. update 실행은 `ops.pipeline_run`에 남기지만, ticket의 `source_run_id`는 마지막 bootstrap provenance로 유지한다.

## Status

지원 status:

- `open`
- `in_progress`
- `resolved`
- `ignored`

`resolved`와 `ignored`는 `resolved_at = now()`를 기록한다. `open`과 `in_progress`는 `resolved_at`을 비운다.

## CLI

ticket을 resolved로 변경:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-update \
  --portfolio-name "Long Term Paper" \
  --ticket-id 7001 \
  --status resolved
```

ticket을 처리 중으로 변경:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli portfolio-remediation-ticket-update \
  --portfolio-name "Long Term Paper" \
  --ticket-id 7001 \
  --status in_progress
```

## Output

- `report_name`: `portfolio_remediation_ticket_update`
- `run_id`
- `portfolio_name`
- `ticket_id`
- `status`
- `updated_count`
- `ticket`

`ticket`은 symbol, action, remediation type, suggested runner, status, reason, timestamps를 포함한다.

## Verification

```bash
bash scripts/verify_portfolio_remediation_ticket_update.sh
```

검증은 Docker Postgres에서 migration/seed를 적용하고, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline을 실행한 뒤 coverage-gated portfolio review와 remediation ticket bootstrap을 만든다. 이후 open report에서 ticket id를 찾고 `resolved`로 변경한 뒤 아래를 확인한다.

- update report name `portfolio_remediation_ticket_update`
- update count `1`
- BABA ticket status `resolved`
- BABA ticket `resolved_at` non-null
- resolved report ticket count `1`
- open report ticket count `0`

## Boundaries

- DB schema를 변경하지 않는다.
- remediation을 자동 실행하지 않는다.
- 실거래 주문/체결과 무관하다.
- assignee, note, due date는 아직 저장하지 않는다.
- review action rule, recommendation, thesis, attribution, performance outcome 산식을 변경하지 않는다.

## Next Steps

- assignee/note/due date가 필요하면 `portfolio.remediation_ticket` schema를 확장한다.
- `portfolio-remediation-daily-run` 결과에서 open ticket을 확인한 뒤 필요한 ticket만 명시적으로 update한다.
- dashboard가 생기면 lifecycle action 버튼을 report와 연결한다.
