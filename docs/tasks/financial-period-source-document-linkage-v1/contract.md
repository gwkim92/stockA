# financial-period-source-document-linkage-v1 Contract

## Task Request

- request: `reported-segment-footnote-parser-v1`가 EC2에서 `candidate_count=0`이 된 원인을 해소한다.
- context: parser는 배포되었지만 EC2의 `market.financial_statement_period.source_document_id`가 모두 비어 있고 raw SEC filing document도 없어서 실제 SEC 원문을 읽지 못한다.

## Goal

- goal: SEC filing metadata, companyfacts financial period, raw SEC filing artifact를 하나의 backend operation으로 연결해 `reported-segment-footnote-parser-run`이 실제 후보를 볼 수 있게 한다. 추천 score/weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/financial_period_source_linkage.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_financial_period_source_linkage.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/financial-period-source-document-linkage-v1/*`
  - `docs/plans/2026-05-26-financial-period-source-document-linkage-v1.md`

## Scope

- Add CLI: `stockanalysis-operations financial-period-source-linkage-run`.
- Dry-run reports current period/source/raw linkage coverage.
- Execute mode can:
  - refresh SEC filing metadata for a CIK,
  - rerun SEC companyfacts for the same CIK so accession numbers can link to existing source documents,
  - backfill any remaining financial period source document links using filing date/form/company-name heuristics,
  - raw-fetch a bounded number of linked SEC filings so parser candidates get local artifacts.
- Add the operation to weekly fundamentals cadence/profile before `reported-segment-footnote-parser-run`.

## Non-Goals

- Do not parse footnotes in this task; parser already exists.
- Do not build a full CIK coverage scheduler for every symbol.
- Do not fetch unlimited SEC filings.
- Do not change recommendation score/weight, benchmark/evaluation split, or broker/order flow.
- Do not commit secrets or runtime env values.

## Schema Change Disclosure

- No schema migration is required. Existing `market.financial_statement_period.source_document_id` and `ingest.source_document.raw_storage_uri` are used.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "financial-period-source-linkage-run|reported-segment-footnote-parser-run"`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-period-source-document-linkage-v1`

## Acceptance Criteria

- Dry-run is read-only and reports `source_period_count`, `linked_period_count`, `sec_source_document_count`, `raw_fetch_candidate_count`.
- Execute records `ops.pipeline_run`, refreshes SEC metadata/companyfacts when CIK is supplied, backfills period links, and raw-fetches at most the configured limit.
- Operation returns `recommendation_scoring_mutated=false`.
- Weekly SEC/fundamental profile runs source linkage before reported segment parser.
- Existing parser can discover candidates once linked raw SEC documents exist.
