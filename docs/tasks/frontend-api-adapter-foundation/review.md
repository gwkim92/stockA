# Review

## Review Notes

- `src/stockanalysis/frontend/api_adapter.py`가 contract index를 읽고 exact API path를 linked example JSON으로 resolve한다.
- CLI `list`와 `get --path`가 추가됐다.
- unknown path는 stable error JSON과 exit code 1을 반환한다.
- actual HTTP server나 frontend scaffold는 생성하지 않았다.

## Verification Evidence

- `bash -n scripts/verify_frontend_api_adapter.sh`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_adapter -v`: 통과
- `PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get --path /api/dashboard/today`: 통과
- `bash scripts/verify_frontend_api_adapter.sh`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-adapter-foundation`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음
