# Implementation Plan

1. Add task contract, implementation plan, handoff, and review placeholders.
2. Add SQL pagination window helper tests for `limit + 1` and cursor offset behavior.
3. Wire live adapter collection endpoints to request bounded SQL/report windows and apply SQL pagination metadata.
4. Update cycle/event/performance SQL renderers to page only collection rows while preserving full summaries where applicable.
5. Add remediation ticket report offset support.
6. Add portfolio coverage paged report SQL path that keeps summary over the full filtered set and pages `positions`.
7. Add targeted regression tests and verification script.
8. Update roadmap, verification plan, README, AGENTS, and task handoff/review.
9. Run targeted and full verification before completion.
