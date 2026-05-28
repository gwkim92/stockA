# cycle-map-path-ux-v2 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- `/cycle-map` should read as the causal path map from news and macro/domain/theme nodes to exposed instruments and recommendation evidence.
- `/cycles` remains the theme-level state board.
- No graph, scoring, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: replace the generic review strip with a cycle-map-specific path panel, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not improve graph edge quality or propagation accuracy.
- Detailed source news and validator explanations remain on `/intelligence` and AI evidence pages.
