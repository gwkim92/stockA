# research-detail-investor-reading-path-v1 Handoff

## Current Status

- status: implemented_and_ec2_smoked
- completed: source document, evidence detail, shared evidence path workbench, and stock detail copy now use investor-facing evidence language; local verification, GitHub push, EC2 deploy, EC2 route smoke, and local tunnel smoke passed.
- branch: `develop`

## What Changed

- Source document detail now frames documents as source evidence used by investment reasoning, not as an AI-process inspection screen.
- Evidence detail now describes source, translation, structured evidence, quality gate, recommendation linkage, and order boundary without `AI 해석` wording.
- Shared evidence path workbench accessibility label now uses `투자 근거 판단 경로`.
- Stock detail now uses `근거 상세`, `투자 근거`, and `기업 리서치` labels instead of AI-process labels.
- Read-only/no-order boundary remains visible but is expressed as execution state, not repeated screen-defense copy.

## Boundaries Preserved

- API contracts unchanged.
- Database schema unchanged.
- Scheduler cadence unchanged.
- Recommendation scoring weights unchanged.
- Benchmark definitions, portfolio positions, paper records, broker/order boundary, and live trading unchanged.

## Verification To Run

- exact next step: continue the UX/UI refactor with a larger information-architecture pass for `/intelligence`, `/cycle-map`, and `/market-map`, focusing on what to inspect today and how evidence changes recommendations.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task research-detail-investor-reading-path-v1`
- `git diff --check`

## Verification Evidence

- local passed: `cd apps/web && npm run typecheck`
- local passed: `cd apps/web && npm run build`
- local passed: `git diff --check`
- local passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task research-detail-investor-reading-path-v1`
- pushed commits: `b8dcbec2`, `a5ace0df`, `e241ee5c`
- EC2 deployed commit: `e241ee5c`
- EC2 active services: `stockanalysis-web.service`, `stockanalysis-frontend-api.service`
- EC2 route smoke passed: `/source-documents/source-document-16557`, `/ai-evidence/ai-evidence-1297`, `/stocks/AAPL`
- local tunnel `http://127.0.0.1:13000` route smoke passed for the same three routes.
- forbidden user-facing terms absent on smoke routes: `AI 해석`, `AI 근거`, `뉴스·AI`, `추천 weight`, `이 화면은`

## Remaining Risk

- This is a wording and reading-path pass only. It does not redesign chart composition, data density, or backend evidence quality.
