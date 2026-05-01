# Review

## Review Notes

- `src/stockanalysis/frontend/live_adapter.py`가 remediation ticket report와 portfolio outcome coverage report를 frontend DTO contract로 변환한다.
- `src/stockanalysis/frontend/api_adapter.py`는 기존 fixture default를 유지하면서 `get --source fixture|live|auto`를 지원한다.
- `--source auto`는 supported live path이고 DB command가 있을 때만 live를 시도한다. DB command가 없으면 fixture fallback한다.
- 기존 fixture server와 Next detail routes는 같은 fixture default 경로로 계속 통과한다.
- DB schema, benchmark, evaluation 기준, write endpoint, broker/trading integration은 변경하지 않았다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v`: 통과
- `bash -n scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_outcome_coverage_report -v`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_remediation_ticket -v`: 통과
- `git diff --check`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-adapter`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Residual Risk

- actual Postgres runtime smoke는 이번 task에서 실행하지 않았다. 기존 canonical report 함수의 DB 검증은 각각 `verify_portfolio_remediation_ticket_report.sh`와 `verify_portfolio_outcome_coverage_report.sh`가 담당한다.
- live 지원 endpoint는 2개뿐이다. daily cockpit, data health, events/themes, performance는 아직 fixture 또는 future live adapter 범위다.
