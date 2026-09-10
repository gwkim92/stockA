# Verification

## Local

- Python: 123 tests passed across model settings, all five affected AI areas, model contracts, and frontend API server. Covers saved model in all five subprocess commands, trusted CLI metadata, per-task/default/explicit priority, snapshot consistency, failures, persistence, concurrent revision conflict, audit integrity, revoked/expired credentials, code replay, read-token write rejection and unchanged order write denial.
- Frontend: 14 focused tests passed, including UI save/readback, locked state, conflict error preservation, OAuth secret non-serialization, same-origin enforcement, HttpOnly session exchange and request-size cap.
- Typecheck and Next production build passed. Build adds only the model settings route pair and existing AI page changes; generated `next-env.d.ts` changes are excluded.
- Real local API + Next production server: browser started locked; one-time code unlocked controls; news translation override changed to Luna and persisted after reload. No actual external AI inference in local QA.
- Desktop 1440x1000 and mobile 390x844 inspected. Mobile shows selected Luna, accessible labelled selects and no horizontal overflow. Screenshots are temporary local artifacts pending final production captures.

## Production

Checkout updated to `811ba980`, but separate server build was followed by SSH/web timeouts before any build-completed/activation result. The production model-setting write and real AI smoke remain unverified. See the recovery state in `handoff.md`; do not equate the successful local UI with live availability.

## Continuous verification and deployable artifact

- Follow-up `69d7c608` fixed absent stderr metadata in a mocked provider. Analysis Prompt Quality CI run `34454568956` passed with the installed SDK on Python 3.11 and 3.13.
- `5e549e38` includes the model-settings suite in prompt CI. Local combined regression: 277 tests, zero failures/errors/unexpected IO, one SDK-unavailable skip. Local venv's missing optional agents package is not an actual provider failure.
- Linux runtime artifact CI run `34454905757` passed build/typecheck/package. Artifact commit `5e549e384ff60611e88b4dd22fe62013cbb7d7fa`, build ID `Hn2ruTFaLHoyn1uX8YDDc`, gzip size 3,574,041 bytes, 800 entries. SHA-256 and archive paths verified after download. Stored under `artifacts/ai-model-settings-v1/linux-runtime/`; no runtime credentials or build cache are included.
- Local inspected screenshots and regression report are retained under `artifacts/ai-model-settings-v1/`. These are local fixture QA evidence, not production serving evidence.
- Final CI readback: `34454905672` passed all four Analysis Prompt Quality jobs, including Python 3.11/3.13 and both Postgres contracts. The feature's Web Product Quality run `34454147709` also completed successfully, including browser regressions.
