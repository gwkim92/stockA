# Session Handoff

## Current Status

- 완료: 추천 상세 API와 화면에 `research.equity_research_artifact` 연결을 추가했고, 로컬 계약/타입/빌드/AWH 검증을 통과했다.

## Implementation Notes

- 목적: 추천 상세에서 `거시/테마/뉴스 → 기업 분석 → 재무/밸류에이션 component → thesis/성과` 흐름을 더 명확히 만든다.
- API 필드: `/api/recommendations/{id}` payload의 `equity_research`.
- 화면 섹션: `기업 리서치 연결`.
- recommendation 기준일과 별개로 최신 기업 리서치 artifact를 보여준다. 이는 추천 당시 점수 입력이 아니라 현재 검토용 읽기 전용 분석이다.
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
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-detail-equity-research-link`
- Pending: EC2 pull/rebuild/restart and `/api/recommendations/{id}`, `/recommendations/{id}` smoke.

## Exact Next Step

- exact next step: 변경사항을 commit/push한 뒤 EC2에서 pull, `apps/web` rebuild, FastAPI/Next restart를 수행하고 추천 상세 API/route smoke를 확인한다.
