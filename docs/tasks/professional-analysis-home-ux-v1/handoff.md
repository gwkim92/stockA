# professional-analysis-home-ux-v1 Handoff

## Status

- in progress: home page has been restructured into a research desk layout and local frontend verification passed. EC2 deploy and live browser smoke are next.

## Current Decision

- Rebuild only the home page information architecture first. The current biggest UX failure is that `/` repeats many operational sections and does not clearly say what to inspect first.
- Keep all investment and trading boundaries unchanged.

## Next Step

- exact next step: commit and push to `develop`, deploy to EC2, restart the web service, and run live browser smoke for `/`.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-analysis-home-ux-v1`

## Risks

- This is a home-page UX pass only. The deeper `/intelligence`, `/ai-evidence`, `/cycle-map`, and `/recommendations` pages still need the same treatment in follow-up tasks.
