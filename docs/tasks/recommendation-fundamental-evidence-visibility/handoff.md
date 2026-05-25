# Session Handoff

## Current Status

- 진행 중: 추천 상세 API와 화면에 zero-weight 기업 분석 component visibility를 추가했다. 로컬 검증은 통과했고 EC2 반영과 route smoke가 남아 있다.

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
- Pending: EC2 API/route smoke.

## Exact Next Step

- exact next step: 로컬 검증을 끝낸 뒤 EC2에 반영하고 `/api/recommendations/{id}`와 추천 상세 화면에서 `fundamental_context` 섹션이 실제로 보이는지 확인한다.
