# professional-source-gap-managed-gate-v1 Handoff

## Status

- completed: managed source blocker policy is implemented and local verification passed; EC2 deploy/smoke remains.

## Context

- `data-health-attention-classification-v1` added categories to open gates.
- The next issue is that `professional_source_gap_attention` is still open even when the current source blocker is already guarded.
- EROK must remain visible as a source limitation. The desired change is not deletion or suppression; it is gate policy refinement.
- The implementation adds `attention_required` to `professional_source_gap_prioritization`.
- Current managed cases:
  - operating-company source blocker with professional decision use blocked, paper validation input blocked, and active recommendation professional use blocked.
  - fund/ETF `fund_not_applicable` row with no missing source layers.
- Unmanaged source blockers, coverage gaps, fund source gaps, and gaps still allowed into professional/paper decisions continue to open `professional_source_gap_attention`.

## Exact Next Step

- exact next step: deploy to EC2 and confirm `/api/data-health` no longer includes `professional_source_gap_attention` for the current fully guarded EROK/SPY source-limit state.
