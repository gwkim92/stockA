# recommendation-detail-professional-evidence-v2 Review

## Review Notes

- Added `professional_evidence_audit` to recommendation detail payloads.
- Audit is derived from existing read-only detail state: cycle, news/AI, financial model, peer, valuation, industry, AI research, thesis, paper validation, and source guardrail.
- Added a Korean recommendation detail section showing audit title, coverage ratio, missing/blocked/pending layers, source blocker, and order/weight boundary.
- Preserved `recommendation_weights_unchanged`, `recommendation_scoring_mutated=false`, `automatic_weight_change_allowed=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
