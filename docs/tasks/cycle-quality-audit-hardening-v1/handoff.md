# cycle-quality-audit-hardening-v1 Handoff

## Status

- status: implemented_local_verified
- current status: implemented locally, verified locally, pending commit, merge to `develop`, EC2 deploy, and EC2 smoke.
- in progress: implemented locally and pending EC2 live database audit smoke.
- updated_at: 2026-06-06
- branch: `codex/cycle-quality-audit-hardening-v1`

## Completed

- `cycle-ai-quality-audit-run` now audits three additional quality risks:
  - `cross_theme_mismatch_count`: strong news/theme incompatibility, such as energy news on quantum cycle or rate/Fed news on energy geopolitics.
  - `duplicate_flow_evidence_count`: the same title split across multiple events and multiple cycle nodes.
  - `weak_propagation_evidence_count`: hierarchical propagation rows with missing source document linkage, low confidence, low impact strength, or weak path weight.
- Audit samples now include `cross_theme_mismatches`, `duplicate_flow_evidence`, and `weak_propagation_evidence`.
- Report `next_actions` now points to the specific remediation path before recommendation input.
- `/data-health` renders the new counters and sample groups in Korean.

## Explicit Non-Changes

- Recommendation score weights unchanged.
- Broker/order boundary unchanged: `read_only_no_order`.
- Portfolio position and benchmark unchanged.
- No data deletion added. Existing cleanup runners remain the only explicit cleanup path.
- No external paid RAG/vector/graph provider added.

## Local Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_ai_quality_audit`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-quality-audit-hardening-v1`

## EC2 Next

- exact next step: commit the local changes, merge to `develop`, deploy to EC2, then run `cycle-ai-quality-audit-run --execute` against the live Postgres database.
- Pull `develop` on EC2 after merge.
- Run `cycle-ai-quality-audit-run --execute --output /opt/stockanalysis/runtime/reports/cycle-ai-quality-audit-latest.json`.
- Smoke `/api/data-health` and `/data-health` for the new counters:
  - `cross_theme_mismatch_count`
  - `duplicate_flow_evidence_count`
  - `weak_propagation_evidence_count`

## Risks

- Cross-theme mismatch rules are intentionally conservative. They catch strong incompatibilities, not every possible bad taxonomy assignment.
- Weak propagation evidence is a warning signal. It should not delete rows by itself because some low-confidence propagation can still be useful as watch evidence.
