# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - `/recommendations/[recommendationId]`에 `상위 흐름 전파 경로` 패널을 추가했다.
  - 기존 `macro_flow_propagation` provenance의 `recent_flows`를 사용하며 API/schema/scoring은 변경하지 않았다.
  - 각 flow row에 테마, 이벤트 제목, 방향, 강도, 신뢰도, 노출도, 발생 시점을 표시한다.
  - EC2에 `d2f3271`를 배포하고 Next.js를 rebuild/restart했다.
  - EC2 API에서 `recommendation-52` / `SPY`가 `macro_flow_score` 전파 근거 8개를 갖는 것을 확인했다.
  - 브라우저에서 `/recommendations/recommendation-52`의 상위 흐름 전파 패널을 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- `/recommendations/[recommendationId]`에서 `macro_flow_propagation` score component를 찾아 별도 패널에 표시한다.
- 각 flow row는 테마, 방향, 강도, 신뢰도, 노출도, 이벤트 제목을 보여준다.
- 기존 score component 목록은 유지하고, 패널은 데이터가 있을 때만 보여준다.

## Verification Log

- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-trace-panel`
- PASS: EC2 `cd apps/web && npm run build`
- PASS: EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`
- PASS: EC2 live API scan
  - `recommendation-52|SPY|8|8`
  - `recommendation-55|XOM|8|8`
  - `recommendation-57|NVDA|7|7`
  - `recommendation-60|MSFT|7|7`
  - `recommendation-61|TSLA|8|8`
- PASS: Browser smoke `http://127.0.0.1:13000/recommendations/recommendation-52`
  - shows `상위 흐름 전파 경로`
  - shows `시장·테마 뉴스가 SPY 점수에 들어간 방식`
  - shows `전파 근거 8개`
  - shows `테마 흐름 보기`

## Remaining

- 다음 범위는 recommendation list에서도 macro-flow evidence 존재를 요약해 사용자가 상세로 들어가기 전 확인할 수 있게 하는 것이다.

## Exact Next Step

- exact next step: add macro-flow evidence count to recommendation list rows and summary.
