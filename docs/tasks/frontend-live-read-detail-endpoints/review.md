# Review

## Review Notes

- `src/stockanalysis/frontend/live_adapter.py`에 recommendation/thesis/AI evidence/source document detail live read 경로를 추가했다.
- recommendation detail은 recommendation batch, score component, linked thesis, latest performance outcome을 읽어 RecommendationDetail DTO로 변환한다.
- thesis detail은 investment thesis, latest thesis review, linked recommendation, event/outcome evidence를 읽어 ThesisDetail DTO로 변환한다.
- AI evidence detail은 extraction artifact, model invocation, prompt template, source chunks, event impact/classification을 읽어 AiEvidenceDetail DTO로 변환한다.
- schema self-review에서 `performance.thesis_outcome.success_grade`와 AI artifact document-link 경로를 반영해 fixture-only 성공을 줄였다.
- source document detail은 source document, retrieval run, chunks, linked AI extraction evidence를 읽어 SourceDocumentDetail DTO로 변환한다.
- DB schema, scoring formula, benchmark/evaluation split은 변경하지 않았다.
- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. 이 slice는 live DTO adapter와 contract shape를 고정하고, 실제 DB smoke는 별도 runtime/data-ops 단계로 남긴다.

## Verification Evidence

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 15 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-detail-endpoints`: 통과.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 279 tests.
