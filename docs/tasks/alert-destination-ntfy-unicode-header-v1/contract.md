# alert-destination-ntfy-unicode-header-v1 Contract

## Task Request

- request: Fix `alert-destination-test-run` failure when the default Korean alert title is sent to `ntfy`.
- context: EC2 `/api/data-health` opened `alert_destination` because the latest passed alert test artifact was older than 168 hours. The required retest failed with `latin-1` header encoding when sending the Korean default title.

## Context

- EC2 `/api/data-health`는 `alert_destination.status=stale_test`를 반환했다.
- 알림 목적지 자체는 `ntfy`로 설정되어 있고 마지막 테스트도 `passed`였지만, 168시간 기준을 넘어 재검증이 필요했다.
- 재검증 실행 시 `latin-1` header encoding error가 발생했다.

## Goal

- goal: Make the free `ntfy` alert test safe for Korean default text by keeping HTTP headers ASCII-only while preserving Korean content in the UTF-8 body, then refresh the EC2 status artifact so `alert_destination` closes.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/alert_destination.py`
  - `tests/test_alert_destination_free_channel.py`
  - `docs/tasks/alert-destination-ntfy-unicode-header-v1/*`

## Invariants

- Do not print or commit alert destination URLs, topics, tokens, or credentials.
- Do not change alert destination target configuration.
- Do not change scheduler cadence.
- Do not change recommendation score weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Add ASCII fallback for `ntfy` title header.
- Preserve non-ASCII title text inside the UTF-8 body.
- Add regression tests for Korean and ASCII `ntfy` titles.
- Re-run the EC2 alert test and verify `/api/data-health.open_gates`.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_alert_destination_free_channel`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task alert-destination-ntfy-unicode-header-v1`
- verification command: EC2 `stockanalysis-operations alert-destination-test-run --execute`
- verification command: EC2 `/api/data-health` smoke
