# Plan

## Steps

1. Create task contract and implementation plan.
2. Add manual host scheduler activation preflight report builder.
3. Add CLI subcommand under `stockanalysis-operations`.
4. Add thin wrapper script.
5. Add unit and CLI tests.
6. Add verification script with repo-outside fixture env/evidence.
7. Update docs, roadmap, README, AGENTS, and verification plan.
8. Run targeted and harness verification.

## Constraints

- Do not run `launchctl`.
- Do not write `~/Library/LaunchAgents`.
- Do not create or modify production env files.
- Do not add scheduler execution into shell wrappers.
- Keep all runtime evidence paths outside the repository.
