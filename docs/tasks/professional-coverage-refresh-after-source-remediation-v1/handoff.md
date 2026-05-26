# professional-coverage-refresh-after-source-remediation-v1 Handoff

## Status

- in progress: contract and plan are opened; EC2 professional coverage refresh after source cleanup is next.

## Context

- `segment-history-source-linkage-remediation-v1` completed with EC2 coverage run `1452`.
- Clean source states now include AAPL/DIS/FANG/GILD `trend_backed`, ADI/AEIS/ALAB/ARM/ELF `single_reportable_segment_no_disaggregated_segment_table`, and EROK `sec_companyfacts_missing_us_gaap_facts`.
- ARM polluted segment labels were removed from `research.segment_footnote_evidence`.

## Exact Next Step

- exact next step: run the bounded professional coverage refresh/evidence checks on EC2 and inspect stock/recommendation DTOs for ARM/EROK-related stale or misleading evidence.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not synthesize segment rows for single-segment companies.
