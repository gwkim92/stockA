# Automation Loop Contract

## Loop

- 이름: portfolio-remediation-daily-automation
- 의도: daily portfolio review 결과를 remediation ticket backlog로 연결한다.
- 실행 주체: 현재는 CLI runner다. 실제 cron, hosted automation, app automation은 별도 승인 후 추가한다.

## Inputs

- portfolio name
- as-of date
- strategy name
- horizon type
- universe version
- optional coverage measurement end date
- ticket limit
- ticket status filter

## Steps

1. `portfolio-review-bootstrap`으로 최신 position snapshot review를 저장한다.
2. `portfolio-remediation-ticket-bootstrap`으로 attention item을 persistent ticket으로 저장한다.
3. `portfolio-remediation-ticket-report`로 unresolved backlog를 조회한다.

## Keep Criteria

- top-level pipeline run status가 `succeeded`다.
- review summary가 생성된다.
- ticket bootstrap summary가 생성된다.
- ticket report가 JSON으로 생성된다.
- open ticket count와 action/remediation type counts가 확인 가능하다.

## Discard Or Retry Criteria

- prerequisite data가 없어 review bootstrap이 실패한다.
- psql execution이 실패한다.
- ticket report payload가 JSON이 아니다.
- top-level pipeline run status가 `failed`다.

## Budget And Safety

- LLM 호출을 사용하지 않는다.
- 외부 네트워크 호출을 추가하지 않는다.
- 실거래 주문/체결을 생성하지 않는다.
- ticket status를 자동으로 resolved/ignored로 바꾸지 않는다.

## Observability

- top-level run: `portfolio_remediation_daily_automation`
- substep runs:
  - `portfolio_review_bootstrap`
  - `portfolio_remediation_ticket_bootstrap`
- output summary:
  - review action counts
  - ticket bootstrap counts
  - ticket report status/action/remediation counts

## Rollback

- runner 자체는 schema를 변경하지 않는다.
- 잘못 실행된 ticket lifecycle 변경은 포함하지 않는다.
- 잘못 생성된 review/ticket rows는 기존 bootstrap provenance로 식별해 별도 운영 절차에서 정리한다.
