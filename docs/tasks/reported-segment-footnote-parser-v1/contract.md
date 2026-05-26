# reported-segment-footnote-parser-v1 Contract

## Task Request

- request: `segment-footnote-extraction-foundation-v1` 이후 남은 핵심 공백인 실제 reported segment metric 추출을 시작한다.
- context: 현재 `research.segment_footnote_evidence`는 SEC filing anchor, consolidated metric, segment data gap을 저장하지만, raw SEC filing footnote/table에서 사업부별 매출·영업이익 같은 `reported_segment_metric`을 생성하지 않는다.

## Goal

- goal: raw SEC filing artifact에서 세그먼트 표를 deterministic parser로 추출해 `research.segment_footnote_evidence.evidence_type='reported_segment_metric'` rows로 저장한다. 이 결과는 기존 SOTP evidence와 valuation UI에 자연스럽게 연결되어야 하며, 추천 score/weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/professional_coverage_expansion.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_professional_coverage_expansion.py`
  - `tests/fixtures/sec_filing_segment_footnote_sample.html`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/reported-segment-footnote-parser-v1/*`

## Scope

- Add backend CLI runner: `stockanalysis-operations reported-segment-footnote-parser-run`.
- Candidate selection uses `market.financial_statement_period.source_document_id` linked to `ingest.source_document.raw_storage_uri`.
- Parser supports local `file://` SEC raw artifacts first.
- Parser extracts simple HTML segment tables with headers such as `Segment`, `Net sales`, `Revenue`, `Operating income`, `Assets`, `Capital expenditures`.
- Upsert extracted rows into `research.segment_footnote_evidence` as `reported_segment_metric`.
- Delete same-date `segment_data_gap` rows for instruments where reported segment metrics were parsed.
- Integrate the step before `segment-footnote-evidence-run`, `sum-of-parts-valuation-run`, and `valuation-snapshot-run`.

## Non-Goals

- Do not build a complete SEC inline XBRL/dimensional taxonomy parser.
- Do not use paid data or paid RAG/vector/graph services.
- Do not treat parser output as final valuation math input yet.
- Do not change recommendation total score, score component weights, benchmark/evaluation split, or broker/order flow.
- Do not expose or mutate secrets.

## Schema Change Disclosure

- No new migration is required. The existing `research.segment_footnote_evidence` table already reserves `reported_segment_metric`.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "reported-segment-footnote-parser-run|segment-footnote-evidence-run"`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-footnote-parser-v1`

## Acceptance Criteria

- Parser dry-run returns candidate count and parsed metric preview without writes.
- Parser execute records `ops.pipeline_run`, upserts `reported_segment_metric` rows, and keeps `recommendation_scoring_mutated=false`.
- Parser ignores unsupported raw URIs safely and reports skipped candidates.
- Existing gap rows for successfully parsed instruments are removed for the same as-of/scope/period to avoid false “segment data gap” display.
- SOTP can observe `reported_segment_metric_count > 0` through the existing evidence table.
- Operating profile runs parser before generic segment evidence and SOTP.
