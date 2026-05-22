# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation detail SQL에 `macro_flow_all_rows`와 `macro_flow_recent_rows`를 추가했다.
  - `propagated_impact_count`는 전체 rows에서 계산하고, `recent_flows`는 최근 8개 preview로 제한했다.
  - 추천 상세 UI에 전체 전파 근거 수와 최근 표시 수가 다를 수 있음을 명시했다.
  - EC2에 배포하고 `/api/recommendations/recommendation-52`와 `/recommendations/recommendation-52` 화면을 검증했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation detail SQL에 `macro_flow_all_rows` CTE를 추가한다.
- `macro_flow_provenance`의 count/source run은 전체 rows에서 계산하고, `recent_flows`만 최근 8개로 제한한다.
- 추천 상세 UI는 “총 N개, 아래는 최근 preview”라고 설명한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-total-count`
- PASS: EC2 deploy to `/opt/stockanalysis/app` at commit `5c3cc54`, `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active.
- PASS: EC2 API smoke `/api/recommendations/recommendation-52` returned `symbol=SPY`, `component=macro_flow_score`, `propagated_impact_count=29`, `recent_flow_count=8`, `first_theme=US_MARKET_BREADTH`.
- PASS: Browser smoke `http://127.0.0.1:13000/recommendations/recommendation-52` showed `상위 흐름 전파 경로`, `시장·테마 뉴스가 SPY 점수에 들어간 방식`, `전체 전파 근거 29개 · 최근 표시 8개`, and preview-count explanation.

## Remaining

- 없음.

## Exact Next Step

- exact next step: continue with the next roadmap task after the macro-flow recommendation list/detail traceability slice.
