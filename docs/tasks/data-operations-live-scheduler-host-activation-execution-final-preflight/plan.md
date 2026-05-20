# Plan

## Steps

1. Create task contract and plan.
2. Add an operations env file loader so CLI commands no longer require shell `source`.
3. Add execution final preflight report builder.
4. Extend `stockanalysis-operations` CLI with `host-activation-execution-final-preflight`.
5. Add a thin shell wrapper that delegates to the operations CLI.
6. Add unit tests for pass/block/error cases.
7. Add verification script that builds the repo-outside activation evidence chain and runs final preflight.
8. Update roadmap, README, AGENTS, verification plan, and task handoff.
9. Run targeted, roadmap, AWH, regression, and diff checks.

## Guardrails

- Do not execute `launchctl`.
- Do not write LaunchAgents.
- Do not execute child data operation commands in the final preflight task.
- Do not add FastAPI write APIs.
- Do not change DB schema, scoring, benchmark, or evaluation split.
