# Implementation Plan

## Steps

1. Create task contract and handoff skeleton.
2. Fix scheduler activation request command preview from quoted `~` to `$HOME`.
3. Add tests/assertions that generated exact commands are shell-safe.
4. Create `/private/tmp/stockanalysis-runtime` venv/env artifacts outside repo.
5. Run available backend/frontend/data-operations smoke checks.
6. Update handoff and roadmap with results and blockers.

## Guardrails

- Do not run `launchctl`.
- Do not write LaunchAgents.
- Do not commit or print real secrets.
- Prefer Python 3.13 over default Python 3.14.
