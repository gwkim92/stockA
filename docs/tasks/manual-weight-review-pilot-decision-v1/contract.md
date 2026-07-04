# manual-weight-review-pilot-decision-v1 Contract

## Purpose

`manual-weight-review-pilot-v1`를 바로 실행할지 판단하고, 실행 전 승인 조건과 금지 조건을 고정한다.

## Task Request

- request: Recommendation outcome sample is ready enough for manual review, but weight mutation and the pilot require an explicit approval decision before execution.

`manual-weight-review-pilot-v1` 승인 여부 결정: recommendation outcome sample은 수동 검토 준비 상태지만, 실제 weight 변경 또는 pilot 실행을 시작해도 되는지 판단한다.

## Goal

- goal: Manual weight review pilot을 지금 시작하지 않는 결정을 문서화하고, 사용자가 승인해야 하는 조건과 계속 금지되는 행동을 명확히 남긴다.

Manual weight review pilot을 지금 시작하지 않는 결정을 문서화하고, 사용자가 승인해야 하는 조건과 계속 금지되는 행동을 명확히 남긴다.

## Mutable Surface

- mutable surface:
  - `docs/tasks/manual-weight-review-pilot-decision-v1/`
  - `docs/tasks/ai-batch-provider-fallback-hardening-v1/handoff.md`

- `docs/tasks/manual-weight-review-pilot-decision-v1/`
- `docs/tasks/ai-batch-provider-fallback-hardening-v1/handoff.md`

## Current Decision

Manual weight review pilot은 아직 시작하지 않는다.

## Evidence To Consider

- Recommendation outcome calibration is ready enough for manual review.
- Portfolio feedback calibration is still explicitly blocking weight review.
- Automatic weight change remains forbidden.
- Broker submit remains forbidden.
- Order boundary remains read-only.

## Start Conditions

Manual pilot can start only after explicit user approval of:

- scope of weights/components to inspect,
- maximum allowed proposed delta,
- evaluation horizon,
- rollback criteria,
- confirmation that changes remain `read_only_no_order`,
- confirmation that no broker submit or automatic order flow is enabled.

## Non Goals

- No scoring weight mutation.
- No automatic weight change.
- No broker submit.
- No recommendation/order execution by AI.

## Verification

- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task manual-weight-review-pilot-decision-v1`

```bash
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task manual-weight-review-pilot-decision-v1
```
