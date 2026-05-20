# Plan

## Steps

1. Create task contract documenting why the roadmap is temporarily interposed before execution final preflight.
2. Add `stockanalysis-operations` console entrypoint.
3. Add shared operations path policy for repo-outside file/output validation.
4. Add shared JSON report IO helpers.
5. Add operations CLI with `cadence`, `run`, `env-readiness`, and `host-activation-execution-decision` commands.
6. Refactor `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh` into a thin CLI wrapper.
7. Add unit tests for CLI behavior and Python repo-outside path enforcement.
8. Update verification script, roadmap, README, AGENTS, and verification plan.
9. Run targeted and regression verification.

## Guardrails

- Do not add FastAPI write routes in this task.
- Do not install scheduler or run `launchctl`.
- Do not write host LaunchAgents.
- Do not change schema, scoring, benchmark, or evaluation split.
- Keep shell scripts only as verify entrypoints or thin wrappers.
