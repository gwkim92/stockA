# ux-copy-system-and-glossary-v1 Handoff

## Status

- completed: local implementation, GitHub push, EC2 deploy, web service restart, EC2 route smoke, and local tunnel smoke are complete.
- current status: completed.

## Current Decision

- Start with primary visible copy only. Full information architecture redesign follows separately in `news-ai-information-architecture-v4` and `data-health-decision-gate-redesign-v2`.

## Next Step

- exact next step: start `news-ai-information-architecture-v4` to reduce duplicated explanations across news/AI pages and add cluster-level Korean translation fallback.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ux-copy-system-and-glossary-v1`
- passed: `git diff --check`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service` returned `active`.
- passed on EC2 and local tunnel: `/`, `/intelligence`, `/ai-evidence/ai-evidence-251`, `/recommendations`, `/stocks/SPY`, `/portfolio/coverage`, `/trading-readiness` rendered new terminology matches.

## Risks

- Copy changes can make operational details too vague. Preserve blocker meanings and order boundaries while changing the wording.
- `/data-health` still contains deeper operational terms. That route needs its own redesign task rather than piecemeal copy edits.
