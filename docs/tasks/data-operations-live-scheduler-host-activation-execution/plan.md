# Plan

## Steps

1. Create task contract and plan.
2. Add host activation execution gate report builder.
3. Extend `stockanalysis-operations` CLI with `host-activation-execution`.
4. Add a thin shell wrapper.
5. Add unit tests for missing confirmation, confirm, abort, malformed path, and secret rejection.
6. Add verification script that uses repo-outside final preflight evidence and confirmation records.
7. Update roadmap, README, AGENTS, verification plan, and task handoff.
8. Run targeted, roadmap, AWH, regression, and diff checks.

## Guardrails

- Do not execute `launchctl`.
- Do not write LaunchAgents.
- Do not execute child data operation commands.
- Do not add FastAPI write APIs.
- Do not change DB schema, scoring, benchmark, or evaluation split.
