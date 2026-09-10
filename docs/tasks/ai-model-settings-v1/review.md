# Review

- All five concrete Codex adapters enter the same settings snapshot before constructing a command. Explicit model flags remain supported; settings cannot inject arguments because writes are constrained to catalog model identifiers.
- Authentication is scoped to settings. A frontend viewer cannot mutate using the server read token; no generic admin token is proxied. One-use codes are redeemed atomically, sessions expire/revoke, and the cookie cannot be read by page JavaScript.
- Same-origin write validation rejects missing/mismatched Origin, cross-site metadata, public HTTP and oversized bodies. Production credentials are never in client props or response JSON.
- Settings and audits commit atomically with optimistic revision checks. DB history failure is displayed independently of settings availability. Unknown prior runtime models are not backfilled with guessed values.
- No recommendation, benchmark, evaluation split, broker/order or billing changes. SDK alternatives retain existing provider policy; the feature is specifically for the authenticated Codex path.
- The last successful provider adapter call is distinct from the latest business DB invocation and from a selected model awaiting execution. Interrupted processes may retain a running record; UI describes this as running or missing termination observation.

Local review found the old registry page assumed there could be no buttons. Its secret-serialization test now isolates the unchanged OAuth panel, while separate model settings component/API tests exercise the new authorized controls. Legacy role cards are collapsed and relabelled as design policy to avoid confusing them with serving evidence.

Deployment and final browser evidence are recorded in `qa.md` and `handoff.md`.
