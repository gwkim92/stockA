# Implementation Plan

## Steps

1. Add `server_scheduler_invocation.py` report builder and markdown renderer.
2. Add `server-scheduler-invocation-plan` CLI.
3. Add focused unit and CLI tests.
4. Add verification script and route it into roadmap verification.
5. Update roadmap, verification plan, AGENTS immediate task, handoff, and review docs.

## Security Notes

- Do not parse or print env file values.
- Treat command/manifest previews as metadata only.
- Keep all runtime evidence paths outside the repository.
- Do not execute generated commands in this task.
