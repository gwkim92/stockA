# recommendation-detail-decision-waterfall-v3 Handoff

## Status

- in progress: 추천 상세 상단에 의사결정 waterfall과 다음 확인 위치를 추가하는 작업을 진행 중이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/recommendations/[recommendationId]` hero 직후 `추천 결론` waterfall 패널을 추가했다.
- completed: `거시`, `테마`, `기업`, `재무`, `밸류에이션`, `리스크`, `페이퍼 검증` 단계를 분리했다.
- completed: 각 waterfall 단계에서 관련 상세 섹션 또는 페이퍼 거래 화면으로 이동하는 링크를 추가했다.
- completed: 전문 흐름, 재무 모델, 밸류에이션, 사이클, 기업 리서치, 상위 흐름, 근거 검토 섹션에 앵커를 추가했다.
- completed: 모바일에서 waterfall 패널과 카드가 1열로 내려가도록 CSS를 추가했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-decision-waterfall-v3`
- passed: `git diff --check`
- pending: EC2/local tunnel `/recommendations/recommendation-157` route smoke

## Next Step

- exact next step: 변경사항을 commit/push/deploy한 뒤 EC2/local tunnel `/recommendations/recommendation-157` route smoke로 새 waterfall 패널과 문구를 확인한다.
