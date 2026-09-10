# Verification

## Local

- Python: 123 tests passed across model settings, all five affected AI areas, model contracts, and frontend API server. Covers saved model in all five subprocess commands, trusted CLI metadata, per-task/default/explicit priority, snapshot consistency, failures, persistence, concurrent revision conflict, audit integrity, revoked/expired credentials, code replay, read-token write rejection and unchanged order write denial.
- Frontend: 14 focused tests passed, including UI save/readback, locked state, conflict error preservation, OAuth secret non-serialization, same-origin enforcement, HttpOnly session exchange and request-size cap.
- Typecheck and Next production build passed. Build adds only the model settings route pair and existing AI page changes; generated `next-env.d.ts` changes are excluded.
- Real local API + Next production server: browser started locked; one-time code unlocked controls; news translation override changed to Luna and persisted after reload. No actual external AI inference in local QA.
- Desktop 1440x1000 and mobile 390x844 inspected. Mobile shows selected Luna, accessible labelled selects and no horizontal overflow. Screenshots are temporary local artifacts pending final production captures.

## Production

Deployment and actual model switching verified on 2026-09-10. Runtime `f9f1d5ee`, Linux web build `Hn2ruTFaLHoyn1uX8YDDc`. Personal EC2 recovered with one console reboot after the initial build stalled; no second server build was run. See `handoff.md` for incident evidence and remaining uncertainty.

- Owner Chrome: locked controls → one-use code → translation Luna override saved at revision 1 → actual adapter success with CLI/model `gpt-5.6-luna` → inherited Terra saved at revision 2 → actual adapter success with CLI/model `gpt-5.6-terra`. Grounded Korean output in both, no business DB writes.
- Final owner reload: authorized, default Terra, zero overrides, both audit entries visible. Observed translation model Terra; unobserved workloads retain explicit uncertainty and older DB records.
- Business history regression: PostgreSQL pool returned Python representations of JSONB without a text cast. `f9f1d5ee` adds `::text`; live `history_available=true`, four historic workload records visible, SEC has no matching invocation. Added history availability/error isolation test; all 6 focused tests passed locally and on Python 3.12 EC2.
- API ready and web home/model page return 200; three API/web services active; all 13 pre-existing active timers restored; settings file mode 0600 and shared path verified.
- Real desktop 1440x1000 and mobile 390x844: viewport width equals document width; five workload controls rendered. Screenshots visually inspected. The separate QA browser remained locked while user Chrome retained its scoped session.
- Evidence: `artifacts/ai-model-settings-v1/production-verification.json`, `production-desktop.png`, `production-mobile-top.png`, `production-mobile-translation.png`. The mobile translation capture was taken between restoring Terra and its next execution, accurately displaying last successful Luna and pending confirmation; later desktop/owner readback shows actual Terra.
- Initial smoke recorder had a label-shadow error after the provider returned; it was fixed and remains a failed telemetry attempt. The two final successful results above are separate, timestamped checks.

## Continuous verification and deployable artifact

- Follow-up `69d7c608` fixed absent stderr metadata in a mocked provider. Analysis Prompt Quality CI run `34454568956` passed with the installed SDK on Python 3.11 and 3.13.
- `5e549e38` includes the model-settings suite in prompt CI. Local combined regression: 277 tests, zero failures/errors/unexpected IO, one SDK-unavailable skip. Local venv's missing optional agents package is not an actual provider failure.
- Linux runtime artifact CI run `34454905757` passed build/typecheck/package. Artifact commit `5e549e384ff60611e88b4dd22fe62013cbb7d7fa`, build ID `Hn2ruTFaLHoyn1uX8YDDc`, gzip size 3,574,041 bytes, 800 entries. SHA-256 and archive paths verified after download. Stored under `artifacts/ai-model-settings-v1/linux-runtime/`; no runtime credentials or build cache are included.
- Local inspected screenshots and regression report are retained under `artifacts/ai-model-settings-v1/`. These are local fixture QA evidence, not production serving evidence.
- Final CI readback: `34454905672` passed all four Analysis Prompt Quality jobs, including Python 3.11/3.13 and both Postgres contracts. The feature's Web Product Quality run `34454147709` also completed successfully, including browser regressions.

- Final backend fix CI: Analysis Prompt Quality `34459033101` and Evaluation History `34459033089` both passed on `f9f1d5ee`. No web source changed after the successful full web CI and Linux build.
