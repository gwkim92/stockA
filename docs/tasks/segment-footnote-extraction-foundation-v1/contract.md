# segment-footnote-extraction-foundation-v1 Contract

## Task Request

- request: `sum-of-the-parts-valuation-foundation-v1` 이후 남은 핵심 공백인 SEC 세그먼트/footnote 근거를 canonical evidence layer로 저장한다.
- context: 현재 SOTP는 영업 FCF, 재무상태 조정, 세그먼트 데이터 공백 reserve로 구성된 proxy다. 이 작업은 실제 사업부별 footnote parsing 전체가 아니라, SEC filing/source document와 consolidated financial metric을 SOTP 근거로 연결하고 segment data gap을 명시적으로 추적하는 foundation이다.

## Goal

- goal: `research.segment_footnote_evidence`에 SEC 공시 기반 segment/footnote evidence rows를 저장하고, SOTP valuation assumptions/DTO/UI가 해당 evidence count, source filing, gap status를 보여준다. 추천 score, score weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `db/migrations/0026_segment_footnote_evidence.sql`
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/professional_coverage_expansion.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/components/valuation-target-range-card.tsx`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_professional_coverage_expansion.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/segment-footnote-extraction-foundation-v1/*`
  - `docs/plans/2026-05-26-segment-footnote-extraction-foundation-v1.md`

## Scope

- Add `research.segment_footnote_evidence`.
- Add backend CLI runner: `stockanalysis-operations segment-footnote-evidence-run`.
- Generate deterministic evidence from existing public data:
  - SEC source filing anchor from `market.financial_statement_period.source_document_id`.
  - consolidated financial metric evidence from `market.financial_metric_value`.
  - explicit `segment_data_gap` rows when no true reported segment metric exists.
- Extend SOTP valuation assumptions with segment evidence metadata.
- Extend frontend valuation payload/card so stock, recommendation, and thesis pages show segment/footnote evidence in Korean.

## Non-Goals

- Do not claim proxy data is true segment-level data.
- Do not build a full HTML/XBRL footnote parser in this task.
- Do not use paid external data or paid RAG/vector/graph services.
- Do not change recommendation total score or component weights.
- Do not change benchmark/evaluation split.
- Do not enable automatic order creation or live broker submit.

## Schema Change Disclosure

- Adds table `research.segment_footnote_evidence`.
- The table is read-only research evidence and does not directly mutate recommendation scoring.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `bash scripts/verify_migrations.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-footnote-extraction-foundation-v1`

## Acceptance Criteria

- Migration creates `research.segment_footnote_evidence` with source document, metric, confidence, and gap fields plus lookup indexes.
- Segment footnote runner dry-run returns coverage preview without writes.
- Segment footnote runner execute records `ops.pipeline_run`, upserts evidence rows, and keeps `recommendation_scoring_mutated=false`.
- SOTP runner and valuation snapshot assumptions include segment evidence metadata where available.
- Frontend valuation payload exposes segment/footnote evidence without breaking older snapshots.
- Shared valuation card renders segment/footnote evidence in Korean.
- Existing order boundary remains `read_only_no_order`.
