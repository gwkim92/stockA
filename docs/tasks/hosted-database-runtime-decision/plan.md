# Implementation Plan

## Steps

1. Add `hosted_runtime_decision.py` report builder and markdown renderer.
2. Add `hosted-database-runtime-decision` CLI.
3. Add focused unit and CLI tests.
4. Add verification script.
5. Update roadmap, verification plan, AGENTS immediate task, handoff, and review docs.

## Decision Rules

- Default zero-budget path recommends Supabase Free Postgres + GitHub Actions worker setup, but marks setup as required.
- If hosted DB is already configured, move to hosted DB migration/smoke.
- If an existing runtime host is available, prefer existing host + systemd worker.
- If local-only is accepted, keep the external scheduler explicitly disabled.
