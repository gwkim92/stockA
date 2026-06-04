# live-ai-invocation-health-remediation-v1 Handoff

## Status

- in progress: local implementation and focused verification are done; EC2 deploy and live smoke remain.

## Current Status

- completed: Reconnected to EC2 from home and restored the local tunnel at `http://127.0.0.1:13000`.
- completed: Confirmed `/api/data-health` has two open gates: `live_ai_invocation_health_attention` and `active_recommendation_price_freshness_attention`.
- completed: Confirmed latest AI health failure is `news-rss-korean-translation`, not OAuth login failure.
- completed: Confirmed root cause: document `15052` has no explicit `AI` token, but Codex OAuth translation output inferred `AI`; validator correctly rejected it.
- completed: Hardened the translation prompt and added one strict retry path after grounding validation failure.

## Remaining

- Run local unit tests and compile verification.
- Commit and deploy to EC2.
- Run EC2 translation smoke and verify `live_ai_invocation_health_attention` is closed or downgraded to recovered state.
- Then handle `active_recommendation_price_freshness_attention` for stale `AVGO`, `BE`, and `DG` prices.

## Exact Next Step

- exact next step: Run AWH verify again, then commit and deploy the translation hardening patch to EC2.

## Boundaries

- Recommendation scoring weights are unchanged.
- Broker/live order submit remains blocked.
- Failed model invocation history is retained for audit.
