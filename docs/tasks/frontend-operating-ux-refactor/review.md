# Review Notes

## Summary

- The global header now groups pages by operating flow instead of exposing every page as a flat numbered list.
- Global typography and card/list text now use safer Korean line wrapping and overflow behavior.
- Key copy now explains the product flow in operator language: data collection, news grouping, individual news AI candidates, recommendations, holding review, and trade safety.
- Individual news candidate analysis is explicitly described as the `/events` AI candidate link leading to `/ai-evidence/:id`.

## Verification

- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
- `git diff --check`: pass.

## Remaining Risks

- EC2 deploy and browser smoke are pending.
- This slice does not change backend data, scoring, scheduler cadence, or broker/order flow.
