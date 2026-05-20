# Scheduler Activation Data Health Visibility Plan

## Steps

1. Add a sanitized approval gate loader to the frontend live adapter.
2. Extend the DataHealth TypeScript type and API example.
3. Render scheduler activation status on `/data-health`.
4. Add focused live adapter tests for configured, missing, and invalid approval gate reports.
5. Wire the local FastAPI env to the repo-outside pending approval gate report and verify through API/browser.

## Non-Goals

- Actual scheduler activation.
- User approval record creation.
- Scheduler mutation endpoints.
- New database tables.
