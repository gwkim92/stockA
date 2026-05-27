# ai-evidence-detail-review-ux-v4 Handoff

## Status

- in progress: AI 근거 상세 상단을 4단계 판단 패널로 재구성하는 작업을 진행 중이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/ai-evidence/[evidenceId]` hero 직후 `AI 근거 결론` 패널을 추가했다.
- completed: `원천·번역`, `AI 구조화`, `자동 검증`, `종목·추천 연결` 4단계 판단 카드를 추가했다.
- completed: 원천 번역, 구조화 필드, 종목 연결, 검증/안전장치 섹션으로 이동하는 앵커를 추가했다.
- completed: 기존 상단 review panel과 trace board 호출을 새 결론 패널로 대체해 첫 화면 중복을 줄였다.
- completed: 모바일에서 결론 패널과 카드가 1열로 내려가도록 CSS를 추가했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-detail-review-ux-v4`
- passed: `git diff --check`
- pending: EC2/local tunnel `/ai-evidence/ai-evidence-251` route smoke

## Next Step

- exact next step: 변경사항을 commit/push/deploy한 뒤 EC2/local tunnel `/ai-evidence/ai-evidence-251` route smoke로 새 결론 패널과 문구를 확인한다.
