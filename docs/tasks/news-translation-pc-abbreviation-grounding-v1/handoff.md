# news-translation-pc-abbreviation-grounding-v1 Handoff

## Current Status

- status: in_progress
- in progress: root cause identified and local code/test change is being verified.
- current status: EC2 translation failure is a validator false positive for `personal computers -> PC`, not a Codex OAuth authentication failure.

## Evidence

- EC2 `/api/data-health.open_gates=["live_ai_invocation_health_attention"]`.
- Latest failed task: `news-rss-korean-translation`.
- Latest error: `news translation output contains ungrounded latin token(s) for document_id=14457: pc`.
- `document_id=14457` source title: `Microsoft, Dell, and HP stocks rise as Nvidia announces new AI chip for personal computers`.
- The same document already has successful AI extraction artifact linked to `NVDA`, `TECH_DOMAIN`, and `TECHNOLOGY`.
- Repeated failures share the same request hash, indicating deterministic retry of the same validator failure.

## Decision

- Treat this as a narrow grounding alias issue.
- Allow `pc`/`pcs` only when source tokens include `personal` and `computer`/`computers`.
- Keep the existing guard against invented entities such as `SpaceX`, `Starlink`, or unsupported tickers.

## Verification Log

- pending.

## Next Step

- exact next step: run local tests, deploy to EC2, rerun bounded translation, then confirm `/api/data-health` no longer opens `live_ai_invocation_health_attention`.
