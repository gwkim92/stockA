# AI model settings

## Request and scope

Expose the five implemented external AI workloads, configured model, and observed CLI model in `/admin/ai-agents`. Allow the owner to choose a shared Codex model or a workload override. Preserve Terra as the initial default. An explicit CLI model still overrides the saved setting.

Add a narrowly scoped model-manager session, atomic durable settings, revision conflict checks, and an append-only audit history. Settings apply to the next invocation; running calls retain their starting revision. No inference is initiated by a settings request.

## Boundaries

Provider selection, OAuth credentials, billing, recommendation weights, benchmarks, evaluation splits, and order submission remain outside this change. Existing fixture and OpenAI SDK alternatives must be identified accurately. Declared agent roles must not be represented as observed live calls.

## Acceptance

- All five Codex invocation adapters use the shared resolver and record selected/CLI-observed models separately. Future business invocation records use transport model metadata rather than the output's self-reported model.
- Server-side SQLite outside the checkout stores revisions, changes, sanitized invocation metadata, model catalog and hashed access/session credentials. Backend API and batch workers use the same configured file.
- Writes require a model-manager session; ordinary read-token access is insufficient. Same-origin browser handlers use an HttpOnly SameSite cookie and never return service credentials.
- Model choices come from the authenticated CLI model catalog; hidden models are excluded. Invalid choices, stale revisions, expired credentials and cross-origin writes are rejected.
- UI covers loading, unavailable storage/catalog, locked/unlocked, save pending/success/error, inherited overrides and audit history; verify desktop/mobile and actual save/readback.
- Relevant Python and frontend checks, production health and bounded actual model execution are recorded separately.
