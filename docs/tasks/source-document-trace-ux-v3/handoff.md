# source-document-trace-ux-v3 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- Source documents should be read as proof inputs for AI evidence, not recommendation or order approval screens.
- Existing source excerpts and linked AI evidence remain read-only.

## Next Step

- exact next step: add the source-document command panel and anchors, run local verification, deploy to EC2, smoke a known source document route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not improve source document extraction or translation quality.
- Some source documents may still lack Korean summaries and must fall back to inferred Korean digest copy.
