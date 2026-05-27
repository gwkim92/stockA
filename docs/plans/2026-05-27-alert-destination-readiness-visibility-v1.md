# Alert Destination Readiness Visibility v1

## Summary

- Goal: replace the static `alert_destination` open gate with explicit readiness evidence.
- The gate must remain open unless an external alert destination is configured and a recent reachability test passed.
- Local-only logs or files can be shown as partial evidence, but they must not close the production alert gate because they do not notify the operator when EC2 or schedulers fail.

## Scope

- Add `alert_destination` payload to `/api/data-health`.
- Read non-secret environment flags and an optional repo-outside status artifact.
- Keep destination secrets redacted. Expose booleans and destination type only.
- Show alert readiness in `/data-health`.
- Add unit tests for missing, local-only, and externally verified alert destinations.

## Non-Goals

- Do not create paid alerting infrastructure.
- Do not store webhook URLs, email credentials, or tokens in the repo.
- Do not enable automatic orders, rebalance actions, or recommendation weight changes.

## Expected Policy

- Ready only when:
  - `STOCKANALYSIS_ALERT_DESTINATION_MODE` is `webhook`, `email`, `telegram`, `slack`, or `discord`.
  - A destination target is configured.
  - A status artifact reports `last_test_status=passed`.
- If mode is `local_file` or `journal`, the system may record local evidence but the gate remains open.
