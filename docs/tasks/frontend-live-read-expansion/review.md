# Review

## Review Notes

- `src/stockanalysis/frontend/live_adapter.py`에 dashboard/data-health live read 경로를 추가했다.
- dashboard는 `portfolio.portfolio`, latest `portfolio.position_snapshot`, latest `portfolio.review`, open `portfolio.remediation_ticket`, latest daily pipeline run을 읽어 기존 DailyCockpit DTO로 변환한다.
- data-health는 latest `ops.pipeline_run`, `market.daily_price_bar`, `portfolio.position_snapshot` freshness를 읽고 production gate가 남아 있음을 `attention_required`와 `open_gates`로 노출한다.
- DB schema, scoring formula, benchmark/evaluation split은 변경하지 않았다.
- actual external Postgres runtime smoke는 이번 task에서 실행하지 않았다. 이 slice는 live DTO adapter와 contract shape를 고정하고, 실제 DB smoke는 별도 runtime/data-ops 단계로 남긴다.

## Verification Evidence

- `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`: 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과, 7 tests.
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-expansion`: 통과.
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 결과 없음.
- `git diff --check`: 통과.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: 통과, 271 tests.
