# reported-segment-footnote-parser-v1 Plan

## Summary

Implement the first deterministic parser for reported SEC segment metrics. The parser reads local raw SEC filing artifacts, extracts straightforward segment tables, stores rows as `reported_segment_metric`, and removes obsolete same-period segment gap rows. This strengthens SOTP evidence without changing scoring weights or order boundaries.

## Implementation

- Add `reported-segment-footnote-parser-run` to `stockanalysis-operations`.
- Select candidates from `market.financial_statement_period` joined to `ingest.source_document.raw_storage_uri`.
- Parse simple HTML tables with segment labels and supported metric headers.
- Upsert rows into `research.segment_footnote_evidence`.
- Integrate the parser before generic segment evidence, SOTP valuation, and valuation snapshots in cadence/profile/professional coverage paths.

## Guardrails

- No recommendation scoring or score weight mutation.
- No benchmark/evaluation split change.
- No broker/order flow change.
- No paid external data dependency.

## Follow-Up

- Improve financial period to source document linkage where missing.
- Add richer inline XBRL/dimensional taxonomy parsing if real filings require it.
- Consider true segment-level SOTP math only after parser coverage and validation improve.
