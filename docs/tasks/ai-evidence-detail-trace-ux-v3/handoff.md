# ai-evidence-detail-trace-ux-v3 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- The existing `EvidenceVisibilityTraceBoard` should become the main transition between the brief and detailed evidence sections.
- Individual evidence detail remains read-only. It shows source and linkage evidence but does not approve recommendations or orders.

## Next Step

- exact next step: render the visibility trace board, remove duplicate summary/question blocks, run local verification, deploy to EC2, smoke a known AI evidence detail route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not alter evidence data or validator decisions.
- Some older evidence records may have sparse visibility trace fields; existing fallback copy must remain safe.
