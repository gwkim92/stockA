# Verification

## Local

- Python: 123 tests passed across model settings, all five affected AI areas, model contracts, and frontend API server. Covers saved model in all five subprocess commands, trusted CLI metadata, per-task/default/explicit priority, snapshot consistency, failures, persistence, concurrent revision conflict, audit integrity, revoked/expired credentials, code replay, read-token write rejection and unchanged order write denial.
- Frontend: 14 focused tests passed, including UI save/readback, locked state, conflict error preservation, OAuth secret non-serialization, same-origin enforcement, HttpOnly session exchange and request-size cap.
- Typecheck and Next production build passed. Build adds only the model settings route pair and existing AI page changes; generated `next-env.d.ts` changes are excluded.
- Real local API + Next production server: browser started locked; one-time code unlocked controls; news translation override changed to Luna and persisted after reload. No actual external AI inference in local QA.
- Desktop 1440x1000 and mobile 390x844 inspected. Mobile shows selected Luna, accessible labelled selects and no horizontal overflow. Screenshots are temporary local artifacts pending final production captures.

## Production

Pending deployment and bounded execution verification. Local tests and fixture server results do not establish live serving.
