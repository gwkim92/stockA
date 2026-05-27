# production-api-server-gate-evidence-v1

## Summary

- `production_api_server` open gate를 정적 placeholder가 아니라 실제 FastAPI runtime evidence로 판단한다.
- production profile, live source, read-token auth, explicit CORS origin, DB config, `psycopg_pool` boundary가 확인되면 gate를 닫는다.
- `/api/data-health`와 `/data-health`에 운영 API 서버 증거를 노출한다.

## Scope

- `/api/data-health`에 `production_api_server` payload를 추가한다.
- static `production_api_server` gate를 evidence policy로 제거하거나 유지한다.
- `/data-health` 운영/자동화 영역에 API runtime, auth, DB boundary evidence를 표시한다.
- 테스트는 missing evidence와 production/live/pool evidence 양쪽을 검증한다.

## Non-Goals

- Reverse proxy, TLS, public domain, auth/RBAC 구현은 이번 범위가 아니다.
- FastAPI service unit이나 runtime env를 변경하지 않는다.
- Recommendation scoring, portfolio state, benchmark, broker/order flow를 변경하지 않는다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task production-api-server-gate-evidence-v1`
