# Review

## Review Notes

- `src/stockanalysis/frontend/live_adapter.py`에 cycle list live read 경로를 추가했다.
- cycle list는 `signal.cycle_state_snapshot` 기준일 이하 최신 snapshot을 theme별로 선택하고, 이전 상태와 instrument rollup을 함께 읽는다.
- feature values는 cycle snapshot의 `event_heat_score`, `trend_score`, `valuation_score`/`breadth_score`를 frontend contract의 `features`로 변환한다.
- DB schema, cycle scoring formula, benchmark/evaluation split은 변경하지 않았다.
- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. 이 slice는 live DTO adapter와 contract shape를 고정하고, 실제 DB smoke는 별도 runtime/data-ops 단계로 남긴다.

## Verification Evidence

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 16 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `bash scripts/verify_project_execution_roadmap.sh`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 280 tests.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-cycle-list`: 통과.
- `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
