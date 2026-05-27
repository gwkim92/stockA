# alert-destination-free-channel-v1 Contract

## Task Request

- request: Remaining `alert_destination` gate를 무료 외부 알림 채널로 닫을 수 있게 한다.
- context: `/api/data-health`는 이미 외부 목적지와 최근 passed test artifact가 없으면 `alert_destination` gate를 열어둔다. 지금 필요한 것은 secret-free 테스트 runner와 repo-outside status artifact 생성 경계다.

## Goal

- goal: `stockanalysis-operations alert-destination-test-run`이 무료 webhook/ntfy/Discord/Slack-compatible URL에 테스트 알림을 보내고, URL/token을 노출하지 않는 status artifact를 repo 밖에 남긴다. `/api/data-health`는 이 artifact를 읽어 gate를 닫을 수 있다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/alert_destination.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_alert_destination_free_channel.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/alert-destination-free-channel-v1/*`

## Invariants

- Do not commit webhook URLs, bot tokens, email credentials, or destination secrets.
- Do not print destination URL or token in stdout, reports, `/api/data-health`, or UI.
- Do not introduce paid alerting, PagerDuty, OpsGenie, managed monitoring, or external paid RAG/vector/graph services.
- Do not change recommendation weights, portfolio positions, benchmark composition, thesis state, or broker/order flow.
- Do not enable live broker submit or automatic orders.

## Scope

- Add a backend CLI runner that can dry-run or execute an alert destination reachability test.
- Support generic webhook-compatible targets and `ntfy` as a free no-account option when configured outside the repo.
- Write a sanitized status artifact with mode, destination type, last test status, timestamp, HTTP status class, and no secrets.
- Extend data-health target detection to include `STOCKANALYSIS_NTFY_TOPIC_URL`.

## Verification

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_alert_destination_free_channel tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task alert-destination-free-channel-v1`
