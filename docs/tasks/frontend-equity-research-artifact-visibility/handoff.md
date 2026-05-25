# Session Handoff

## Current Status

- 완료: `research.equity_research_artifact`를 종목 상세 API와 화면에 노출했고, 로컬 계약/타입/빌드/AWH 검증을 통과했다.

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
- Pending: EC2 pull/rebuild/restart and `/stocks/NVDA` route smoke.

## Exact Next Step

- exact next step: 변경사항을 commit/push한 뒤 EC2에서 pull, `apps/web` rebuild, FastAPI/Next restart를 수행하고 `/api/stocks/NVDA`와 `/stocks/NVDA`에서 `AI 기업 분석 리포트`가 보이는지 확인한다.
