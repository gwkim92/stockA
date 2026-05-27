# ux-copy-system-and-glossary-v1 Handoff

## Status

- in progress: commit, EC2 deploy, and route smoke remain.
- local implementation complete; commit, EC2 deploy, and route smoke remain.

## Current Decision

- Start with primary visible copy only. Full information architecture redesign follows separately in `news-ai-information-architecture-v4` and `data-health-decision-gate-redesign-v2`.

## Next Step

- exact next step: commit and push the copy cleanup, pull it on EC2, rebuild/restart `stockanalysis-web.service`, then smoke `/`, `/intelligence`, `/ai-evidence/ai-evidence-251`, `/recommendations`, `/stocks/SPY`.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`

## Risks

- Copy changes can make operational details too vague. Preserve blocker meanings and order boundaries while changing the wording.
- `/data-health` still contains deeper operational terms. That route needs its own redesign task rather than piecemeal copy edits.
