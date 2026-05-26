# reported-segment-parser-quality-v1 Contract

## Task Request

- request: `financial-period-source-document-linkage-v1` 이후 EC2에서 parser candidate는 생겼지만 Apple 10-K의 `reported_segment_metric_count=0`인 문제를 해소한다.
- context: Apple 10-K 원문은 reportable segment가 열 헤더이고 `Net sales`, `Operating income/(loss)`가 행 라벨인 전치형 segment table을 사용한다. 기존 parser는 첫 열이 segment label인 단순 표만 지원한다.

## Goal

- goal: 실제 SEC 10-K에서 흔한 전치형 reportable segment table을 deterministic parser가 읽어 `reported_segment_metric` rows를 생성하게 한다. 이 결과는 SOTP segment evidence 품질을 높이는 입력이며, 추천 score/weight, benchmark, broker/order boundary는 변경하지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/professional_equity_analysis.py`
  - `tests/test_professional_equity_analysis.py`
  - `tests/fixtures/sec_filing_aapl_transposed_segment_sample.html`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/tasks/reported-segment-parser-quality-v1/*`
  - `docs/plans/2026-05-26-reported-segment-parser-quality-v1.md`

## Scope

- Add support for transposed reportable segment tables:
  - first singleton year row, e.g. `2025`;
  - second row segment headers, e.g. `Americas`, `Europe`, `Greater China`, `Japan`, `Rest of Asia Pacific`, `Corporate`, `Total`;
  - metric rows, e.g. `Net sales`, `Operating income/(loss)`;
  - currency marker cells like `$` are ignored during alignment.
- Exclude aggregate/non-operating columns such as `Corporate` and `Total`.
- Preserve existing simple segment table parsing.
- Preserve `recommendation_scoring_mutated=false`.

## Non-Goals

- Do not build a complete inline XBRL dimensional parser in this slice.
- Do not change SOTP valuation math or recommendation score weights.
- Do not add paid data providers or external RAG/vector/graph services.
- Do not mutate broker/order flow.

## Schema Change Disclosure

- No schema migration is required.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis`
- verification command: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-parser-quality-v1`

## Acceptance Criteria

- Unit test proves an Apple-style transposed segment table yields at least `segment_revenue` and `segment_operating_income` for reportable segments.
- Parser excludes `Corporate` and `Total` from reported segment metric rows.
- Existing simple table parser tests still pass.
- EC2 `reported-segment-footnote-parser-run --execute` on the linked Apple 10-K candidate creates `reported_segment_metric_count > 0`.
- No recommendation score/weight, benchmark, or broker/order behavior changes.
