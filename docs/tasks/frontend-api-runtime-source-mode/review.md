# Review

## Review Notes

- `fixture_server.py`가 기존 fixture default를 유지하면서 `source` mode를 받는다.
- `create_frontend_fixture_server(..., source="auto")`는 DB config가 없을 때 fixture payload를 반환한다.
- `create_frontend_fixture_server(..., source="live")`는 DB config가 없을 때 HTTP 503 stable JSON error를 반환한다.
- `/__health`, `/__endpoints`, startup JSON, response header가 source mode를 드러낸다.
- write method는 여전히 405로 막고, auth/RBAC/write endpoint는 추가하지 않았다.

## Verification Evidence

- `PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v`: 통과
- `bash scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_live_read_adapter.sh`: 통과
- `bash -n scripts/verify_frontend_fixture_server.sh`: 통과
- `bash scripts/verify_frontend_detail_routes.sh`: 통과
- `git diff --check`: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-runtime-source-mode`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Residual Risk

- actual DB-backed HTTP live success smoke는 아직 없다. DB command가 있는 환경에서 `--source auto`가 live-supported endpoint를 실제로 읽는 검증은 다음 live endpoint expansion 또는 runtime DB smoke task에서 다룬다.
- local runtime은 production API server가 아니다. connection pooling, auth/RBAC, deployment policy는 남아 있다.
