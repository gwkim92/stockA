# Runtime and evaluation evidence recovery — 2026-09-10

## Request and scope

The user authorized proceeding with the project-analysis priorities: verify current runtime, recover AI and active-recommendation price freshness within existing configuration and budgets, inspect actual evaluation evidence, and record a current handoff. Preserve the pre-existing edit in `docs/tasks/runtime-deploy-20260908/handoff.md`.

## Execution order

1. Verify the existing SSH target's instance identity, deployed revision, service/timer status, API health, provider status, and price/evaluation evidence using read-only probes.
2. Restore the existing local access path and resolve evidenced operational failures within the existing account, configuration, provider budget, and runner boundaries.
3. Inspect canonical evaluation lineage, frozen snapshots, outcome maturity, and prospective-evidence preflight; execute only bounded existing observation/remediation routes supported by current evidence.
4. Verify affected runtime/data/user paths and publish a current handoff with completed, blocked, and unverified items.

## Boundaries

- AWS target is personal account `115623963546`, us-east-1, instance `i-029d51b163fb07b61`; no local AWS CLI writes.
- Do not modify credentials, billing, quota limits, benchmark/evaluation policies, recommendation scoring weights, portfolio positions, or order/broker permissions.
- Do not invoke paid model fallbacks or repeated failed provider calls as a recovery shortcut. User authentication may require direct user participation.
- Keep live access, data writes, model success, local tests, deployment, and evidence validity separate in reporting.
- Defer broad module decomposition until operational findings identify a bounded change; no speculative refactor during diagnosis.

## Approved continuation

On 2026-09-10 the user explicitly approved switching scheduled news work to the authenticated Codex provider and requested identification of the models actually used through authentication. Change only `STOCKANALYSIS_LLM_PROVIDER` from `agents_sdk_openai` to `codex_oauth` in the existing server data operations env, after a server-side backup. Keep schedule, per-run limits, credentials, scoring weights and order permissions unchanged. Verify the generated scheduler commands, a real run using the configured provider and actual selected model metadata; distinguish DB placeholders from resolved model names. This is an explicit exception to the earlier no-provider-configuration-change boundary, not authorization for a model upgrade or billing change.

## Completion criteria

Current evidence identifies service, AI, price, and evaluation status; authorized recoverable failures are addressed and checked; exact external blockers are reported; task handoff links sanitized evidence and any required next action.
