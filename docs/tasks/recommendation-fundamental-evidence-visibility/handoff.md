# Session Handoff

## Current Status

- 완료: 추천 상세 API와 화면에 zero-weight 기업 분석 component visibility를 추가했고, 로컬 검증과 EC2 API/route smoke를 통과했다.

## Implementation Notes

- `recommendation-fundamental-components`가 저장한 5개 component는 추천 결과를 바꾸지 않고, 추천 상세의 전문가식 검토 근거로만 노출한다.
- 새 provenance source type:
  - `fundamental_context`
- 대상 component:
  - `fundamental_quality_score`
  - `valuation_margin_score`
  - `peer_relative_score`
  - `balance_sheet_risk_penalty`
  - `thesis_consistency_score`
- 화면 섹션:
  - `재무·밸류에이션 근거`
  - 문구는 “현재 추천 총점에는 미반영된 검증 항목”으로 고정한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-fundamental-evidence-visibility`
- Passed on EC2: pulled `b008acd`, rebuilt `apps/web`, restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- Passed on EC2 API: `/api/recommendations/recommendation-140` returned `fundamental_context` count `5`, non-zero fundamental weight count `0`.
- Passed on EC2 route smoke: `/recommendations/recommendation-140` rendered `재무·밸류에이션 근거`, `뉴스가 아니라 기업 자체가 받쳐주는가`, `추천 총점에는 아직 미반영`.

## Exact Next Step

- exact next step: 다음 작업은 `ai-equity-research-reporting` 또는 `portfolio-risk-budget` 중 roadmap 우선순위를 선택해 task contract를 만들고, 종목별 사업/재무/밸류에이션 리서치 artifact나 포트폴리오 리스크 한도 중 하나를 실제 데이터와 화면에 연결한다.
