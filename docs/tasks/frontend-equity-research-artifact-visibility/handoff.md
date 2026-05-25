# Session Handoff

## Current Status

- 완료: `research.equity_research_artifact`를 종목 상세 API와 화면에 노출했고, 로컬 계약/타입/빌드/AWH와 EC2 API/route smoke를 통과했다.

## Implementation Notes

- 목적: DB에 생성된 기업 리서치 artifact가 사용자가 보는 종목 화면까지 이어지게 한다.
- 화면 위치: `/stocks/{symbol}`의 가격/추천/뉴스 흐름 사이에 `AI 기업 분석 리포트` 섹션을 둔다.
- API 필드: `/api/stocks/{symbol}` payload에 `equity_research`를 추가한다.
- 화면 내용: 리서치 제목, 한국어 요약, 핵심 포인트, 촉매, 리스크, 무효화 조건, 밸류에이션 민감도, 원천 문서 링크를 보여준다.
- 경계:
  - FastAPI/Next request 중 실시간 AI 호출은 하지 않는다.
  - recommendation score와 weight는 바꾸지 않는다.
  - 실거래 broker submit은 범위 밖이다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-equity-research-artifact-visibility`
- Passed on EC2: pulled `1b2adfd`, rebuilt `apps/web`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- Passed on EC2 service check: both services returned `active`.
- Passed on EC2 API: `/api/stocks/NVDA` returned `equity_research.title = NVDA 기업 리서치 요약`, provider `fixture`, key points `5`, risks `3`, source run `pipeline-run-761`.
- Passed on EC2 route smoke: `/stocks/NVDA` rendered `AI 기업 분석 리포트`, `NVDA 기업 리서치 요약`, `핵심 포인트`, `리스크`.

## Exact Next Step

- exact next step: 다음 작업은 추천 상세에도 `research.equity_research_artifact`를 연결하거나, `portfolio-risk-budget-foundation`으로 넘어가 포트폴리오 리스크 한도/포지션 사이징을 API와 화면에 붙인다.
