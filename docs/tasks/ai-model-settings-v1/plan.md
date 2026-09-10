# Implementation plan

1. Inventory: enumerate production invocation adapters, alternate providers and diagnostic-only calls; distinguish configured values from observed execution.
2. Runtime: implement a small SQLite settings/audit/session store and shared Codex invocation context. Wire all five adapters without changing prompts, validation or business decisions.
3. API: add explicit model-settings routes before the generic read-only catchall. Add same-origin Next handlers, scoped login/logout and no secret serialization.
4. UI: add the live model settings panel above the existing registry, relabel the registry as design policy, show per-workload effective model, observed call, overrides, current revision and recent audit.
5. Verify: persistence/concurrency, unauthorized/expired/session replay, invalid model, model priority and all adapter call paths; typecheck/build and browser interactions.
6. Deploy: back up runtime configuration, share one settings path, refresh catalog without inference, deploy develop at a safe service boundary, unlock the owner's browser with one-time access, run one bounded model switch smoke, restore Terra and record evidence.

## Decisions

Use Python stdlib SQLite for operational model configuration, outside the business Postgres schema and checkout. This keeps scheduler and API reads consistent without rewriting env files on each browser save. Use a one-time server-issued access code to establish a model-settings-only browser session. It grants no OAuth, process execution, billing or order access. Expose a server CLI command to issue a new code after logout/expiry.

The configured model is a request choice. A CLI startup header verifies CLI selection, not provider-side routing; label it accordingly. A failed invocation must never be labelled a successful serving result.
