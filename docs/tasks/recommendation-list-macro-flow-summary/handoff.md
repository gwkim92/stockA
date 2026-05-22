# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - recommendation list SQL에 `macro_flow_component_count`와 `macro_flow_evidence_count`를 추가했다.
  - recommendation list summary에 `macro_flow_evidence_recommendation_count`를 추가했다.
  - `/recommendations` 카드에 상위 흐름 근거 badge와 요약 문구를 표시했다.
  - EC2에 `5308f60`를 배포하고 FastAPI/Next를 rebuild/restart했다.
  - EC2 live API와 브라우저에서 상위 흐름 추천 목록 요약이 표시됨을 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- recommendation list SQL의 score component count에 `macro_flow_component_count`를 추가한다.
- recommendation row 별 propagated impact count를 bounded lateral query로 계산한다.
- `/recommendations` summary와 row card에 상위 흐름 근거 수를 표시한다.

## Verification Log

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-list-macro-flow-summary`
- PASS: EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- PASS: EC2 `cd apps/web && npm run build`
- PASS: EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`
- PASS: EC2 live API `/api/recommendations`
  - `recommendation_count=19`
  - `macro_flow_evidence_recommendation_count=5`
  - `macro_row_count=5`
  - sample: `recommendation-52|SPY|components=1|flows=29`
- PASS: Browser smoke `http://127.0.0.1:13000/recommendations`
  - shows `상위 흐름 연결`
  - shows `거시·테마 전파 근거 보유`
  - shows `상위 흐름 29개`
  - shows `상위 흐름 전파 29개`
  - shows `근거 5개 · 흐름 1개`

## Remaining

- 다음 범위는 추천 목록의 상위 흐름 수가 추천 상세의 recent flow 제한 수와 다르게 보이는 이유를 더 친절히 설명하는 것이다. 현재 목록은 전체 전파 row 수, 상세는 최근 flow preview를 보여준다.

## Exact Next Step

- exact next step: add explanatory copy for total macro-flow count versus detail preview, or continue improving recommendation detail trace links.
