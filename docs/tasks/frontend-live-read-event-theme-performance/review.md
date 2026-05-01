# Review

## Review Notes

- `src/stockanalysis/frontend/live_adapter.py`에 event/theme/performance live read 경로를 추가했다.
- event list는 `event.event`, instrument/classification impact, source document link, AI extraction artifact를 읽어 EventList DTO로 변환한다.
- theme detail은 internal theme node, cycle state snapshot, linked instruments, supporting events를 읽어 ThemeDetail DTO로 변환한다.
- performance outcomes는 attribution run, recommendation outcomes, attribution components, coverage exclusions를 읽어 PerformanceOutcomes DTO로 변환한다.
- DB schema, scoring formula, benchmark/evaluation split은 변경하지 않았다.
- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. 이 slice는 live DTO adapter와 contract shape를 고정하고, 실제 DB smoke는 별도 runtime/data-ops 단계로 남긴다.

## Verification Evidence

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 10 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-event-theme-performance`: 통과.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 274 tests.
