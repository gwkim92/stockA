# research-detail-investor-reading-path-v1 Handoff

## Current Status

- status: implemented_locally_pending_verification
- in progress: source document, evidence detail, and stock detail copy now use investor-facing evidence language; local verification and EC2 deploy remain.
- branch: `develop`

## What Changed

- Source document detail now frames documents as source evidence used by investment reasoning, not as an AI-process inspection screen.
- Evidence detail now describes source, translation, structured evidence, quality gate, recommendation linkage, and order boundary without `AI 해석` wording.
- Stock detail now uses `근거 상세`, `투자 근거`, and `기업 리서치` labels instead of AI-process labels.
- Read-only/no-order boundary remains visible but is expressed as execution state, not repeated screen-defense copy.

## Boundaries Preserved

- API contracts unchanged.
- Database schema unchanged.
- Scheduler cadence unchanged.
- Recommendation scoring weights unchanged.
- Benchmark definitions, portfolio positions, paper records, broker/order boundary, and live trading unchanged.

## Verification To Run

- exact next step: run local typecheck/build/AWH/diff checks, commit, push to `develop`, deploy to EC2, and route-smoke `/source-documents/<id>`, `/ai-evidence/<id>`, `/stocks/<symbol>`.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task research-detail-investor-reading-path-v1`
- `git diff --check`

## Remaining Risk

- This is a wording and reading-path pass only. It does not redesign chart composition, data density, or backend evidence quality.
