# professional-source-gap-prioritization-v1 Handoff

## Status

- pending: this is the immediate next task after `recommendation-outcome-due-cadence-automation-v1`.

## Context

- Outcome weight review remains blocked until 2026-06-20 or later.
- Professional coverage is sufficient for the current guardrail, but visible source blockers remain.
- Known examples: SPY/fund-like products are not applicable to company financial models; EROK lacks SEC companyfacts US-GAAP financial statement facts.

## Exact Next Step

- exact next step: inspect current professional coverage/source blocker payloads and decide whether the prioritization belongs in `/api/data-health`, `/api/stocks`, or a dedicated operations eval.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate missing financial facts.
- Do not classify ETF/fund products as failed company-financial coverage.
