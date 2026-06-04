# ux-information-architecture-reset-v1 Handoff

## Status

- in progress: first news/AI evidence UX slice implemented and locally verified.

## Current Status

- completed: audited 24 routes through the local EC2 tunnel.
- completed: identified systemic issue: repeated giant hero plus 4-card command panel plus long raw ledger.
- completed: selected first implementation slice: `/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results`.
- completed: added compact decision-first layout classes in `apps/web/src/app/globals.css`.
- completed: refactored `/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results` so the first viewport shows conclusion, counts, and next action before raw ledgers.
- completed: fixed blocked evidence count confusion by using total blocked/suppressed count in the headline and marking the ledger as latest displayed rows.

## Exact Next Step

- exact next step: extend the same decision-first pattern to `/`, `/data-health`, `/intelligence`, `/cycle-map`, `/stocks/[symbol]`, `/recommendations/[id]`, and `/paper-trading`.

## Risks

- This slice improves information architecture only. It must not change data, scoring, broker/order boundary, or scheduler behavior.
- Dense raw ledgers are still needed for audit; move them below fold rather than deleting evidence.
- Existing top navigation still wraps awkwardly on narrow mobile widths. It did not overflow horizontally, but it needs a separate navigation cleanup slice.
- Raw ledgers are still dense below the fold. They remain intentionally available for audit, but card internals need a later readability pass.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ux-information-architecture-reset-v1`
- passed: `git diff --check`
- passed: local route smoke against EC2 FastAPI tunnel on `http://127.0.0.1:3002/events`, `/ai-evidence`, `/ai-evidence/blocked`, `/ai-evidence/results`
- passed: mobile smoke for `/events` and `/ai-evidence/blocked`, no horizontal overflow at 390px viewport

## Browser Evidence

- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/events.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence_blocked.png`
- desktop screenshot: `/tmp/stockanalysis-ux-reset-v1-after/ai-evidence_results.png`
- mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-mobile/events.png`
- mobile screenshot: `/tmp/stockanalysis-ux-reset-v1-mobile/ai-evidence_blocked.png`
