# Recommendation evaluation history v1

Base: develop@1d9d8dcc3699152a1fe435a304d95d96d930b9b1 (PR #48).

## Goal
Expose stored recommendation evaluation runs and their frozen recommendation snapshots through the existing authenticated read-only frontend API. This first slice establishes a safe, paginated history contract before adding current-versus-historical comparison UX.

## API
- GET /api/recommendation-evaluations?limit=25&before=<eval-run numeric ID>
- GET /api/recommendation-evaluations/eval-run-<ID>?limit=25&after=<snapshot numeric ID>
- Positive canonical decimal IDs bounded by PostgreSQL bigint; limit 1..100. Reject duplicate, unknown, blank and malformed query parameters before executing SQL.
- Keyset pagination, deterministic ordering, one result SELECT per page after a schema-readiness probe. Pagination metadata describes only the returned page, not an investment performance aggregate.
- Runs are restricted to eval_name=recommendation_quality_calibration. No other eval family can be read through this route.
- Detail reads only ai.eval_run and ai.recommendation_eval_snapshot. It must never substitute today's recommendation, thesis, components or outcomes for absent history.
- Stored IDs are serialized as strings outside raw snapshot_json to avoid JavaScript bigint precision loss.
- Legacy no-snapshot history, recorded-empty history, count mismatch and recorded history are distinct states. Missing migration/source, missing run and genuinely empty history are distinct outcomes.
- Stored snapshot SHA is exposed as an identity only, not cryptographic verification or a semantic-quality assertion. Source IDs are historical values, not guaranteed resolvable links.
- fixture/auto must not silently manufacture successful empty history when a live source is unavailable.

## Boundaries
No schema/migration/seed changes, source backfill, snapshot repair/update/delete, scoring/weights/thresholds/benchmarks, portfolio/order/broker, secrets, paid model calls, production DB, scheduler, main or deployment changes. CI may provision a disposable PostgreSQL database with synthetic data and SELECT-only reader permissions. Existing HTTP authentication, no-store and write rejection remain in force.

## Verification
Unit tests for parser/ID limits, SQL read-only/source isolation, pagination, unavailable/missing/empty distinctions, legacy versus recorded-empty, count mismatch, raw-value preservation and adapter routing. HTTP tests for authentication, GET/error statuses, cache boundary and blocked writes. PostgreSQL integration executes the real checked-in migrations and generated queries in a disposable test database; verifies selected eval isolation, pagination, frozen source survival and least-privilege read behavior. Existing analysis/CLI regression remains a guard.

## Not delivered by this slice
Current-versus-then drift UI, later-outcome comparison, source truth verification and production rollout. These must consume the verified history contract without mutating it.
