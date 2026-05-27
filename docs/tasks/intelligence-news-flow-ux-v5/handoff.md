# intelligence-news-flow-ux-v5 Handoff

## Status

- status: in_progress
- in progress: `/intelligence` 화면을 네 단계 판단 순서로 재구성하는 작업을 진행 중이다.

## Intent

`/intelligence`를 “뉴스와 AI 기능이 많이 있는 화면”이 아니라 “오늘 투자 판단 전에 어떤 흐름과 근거를 봐야 하는지 알려주는 화면”으로 정리한다.

## Boundaries

- 추천 weight, benchmark, portfolio position, broker/order boundary는 변경하지 않는다.
- 화면 문구와 정보 구조만 변경한다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task intelligence-news-flow-ux-v5`
- passed: `git diff --check`

## Next

- exact next step: 변경사항을 커밋하고 EC2에 배포한 뒤 `/intelligence` route smoke를 수행한다.
