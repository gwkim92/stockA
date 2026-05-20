# Task Review

## Summary

- Added read-only evidence quality gates to recommendation and thesis detail DTOs.
- Recommendation detail now shows whether the recommendation has a linked thesis, score components, AI/event evidence, outcome measurement, and an intact no-order boundary.
- Thesis detail now shows whether the thesis has source events, performance evidence, invalidation conditions, recent human review, and an intact no-order boundary.
- Recommendation and thesis pages now render “근거 품질 점검” in Korean so the user can see whether a recommendation/thesis is reviewable or still needs evidence work.

## Verification Evidence

- API/unit: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed.
- Frontend typecheck: `cd apps/web && npm run typecheck` passed.
- Frontend build: `cd apps/web && npm run build` passed.
- Harness: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-thesis-evidence-gates` passed.
- Whitespace/syntax safety: `git diff --check` passed.
- Live API smoke:
  - `/api/recommendations/AAPL-2024-11-01`: `quality_status=needs_evidence_review`, `pass_count=4`, `warning_count=1`, `blocked_count=0`.
  - `/api/theses/AAPL-bootstrap-v1`: `quality_status=ready_for_human_review`, `pass_count=5`, `warning_count=0`, `blocked_count=0`.
- Browser check:
  - Recommendation screenshot: `/private/tmp/stockanalysis-runtime/recommendation-evidence-gates-v2.png`.
  - Thesis screenshot: `/private/tmp/stockanalysis-runtime/thesis-evidence-gates-v3.png`.

## Residual Risks

- This validates evidence coverage but does not generate or improve recommendation scores.
- Recommendation score components still use generic evidence ids for cycle/market features; they need explicit event/AI evidence links before the recommendation can become fully review-ready.
- The gates are deterministic quality-control metadata, not investment advice and not order approval.
