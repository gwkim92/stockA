# Implementation Plan

- `src/stockanalysis/frontend/api_adapter.py`를 만든다.
- adapter는 contract index를 읽고 endpoint path를 example JSON으로 resolve한다.
- CLI `list`와 `get --path`를 제공한다.
- `tests/test_frontend_api_adapter.py`를 만든다.
- `scripts/verify_frontend_api_adapter.sh`를 만든다.
- `docs/frontend-api-adapter.md`, README, frontend docs, verification plan을 갱신한다.
- task handoff/review에 verification evidence를 남긴다.
