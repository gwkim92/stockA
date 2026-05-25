# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - stock detail/recommendation detail live SQL에 `research.industry_competitive_position` 최신 row를 연결했다.
  - `StockDetailData`와 `RecommendationDetailData`에 `industry_competitive_position` DTO를 추가했다.
  - 종목 상세와 추천 상세에서 산업 경쟁 위치, 피어 그룹, 강점, 리스크, 경쟁력/리스크 추정 점수를 한국어로 표시한다.
  - 로컬 focused tests, Next typecheck/build, compileall, diff check, AWH verify를 통과했다.
- 진행 중:
  - EC2 배포와 route smoke가 남아 있다.
- 막힌 점:
  - 없음.

## Decisions

- 산업 경쟁 포지션은 확정 애널리스트 판단이 아니라 피어/재무 기반 deterministic 추정 지표로 표시한다.
- 추천 score/weight는 변경하지 않는다.
- 화면 진입 중 AI를 호출하지 않는다. 배치가 저장한 값을 읽기 전용으로 보여준다.

## Exact Next Step

- exact next step: 로컬 검증과 EC2 배포 smoke를 마친 뒤, 다음 작업은 `recommendation-quality-calibration`으로 돌아가 산업 경쟁 포지션/재무/밸류에이션 점수 항목의 성과 설명력을 측정한다. 추천 가중치는 평가 전까지 계속 0으로 둔다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - 결과: `Ran 58 tests ... OK`
- `cd apps/web && npm run typecheck`
  - 결과: 통과
- `cd apps/web && npm run build`
  - 결과: Next production build 통과
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - 결과: 통과
- `git diff --check`
  - 결과: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task frontend-industry-competitive-position-visibility`
  - 결과: `Task frontend-industry-competitive-position-visibility passed readiness checks.`
