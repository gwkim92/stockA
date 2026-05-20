# Implementation Plan

## Steps

1. Add `server_scheduler_deployment_decision.py` report builder and markdown renderer.
2. Add `server-scheduler-deployment-target-decision` CLI.
3. Add focused unit and CLI tests.
4. Add verification script.
5. Update roadmap, verification plan, AGENTS immediate task, handoff, and review docs.

## Decision Rules

- If an existing runtime host is available, prefer `vps_systemd_timer`.
- If hosted DB/runtime exists and the repo is public, prefer `github_actions_scheduled_workflow`.
- If only the local Mac can reach the DB, mark external scheduler deployment blocked unless local host scheduler is explicitly allowed.
- Never deploy scheduler artifacts in this task.
