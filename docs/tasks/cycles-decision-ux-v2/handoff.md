# cycles-decision-ux-v2 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- `/cycles` should read as the theme-level cycle status board.
- `/cycle-map` should remain the graph/path view for macro-to-theme-to-instrument propagation.
- No scoring, API, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: add the `/cycles` command panel, update responsive CSS, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not improve cycle calculation accuracy.
- Detailed event-to-cycle causality remains on `/cycle-map`, theme detail, and evidence pages.
