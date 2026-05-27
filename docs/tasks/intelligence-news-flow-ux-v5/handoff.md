# intelligence-news-flow-ux-v5 Handoff

## Status

- status: completed
- completed: `/intelligence` 화면을 네 단계 판단 순서로 재구성하는 작업을 완료했다.

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
- passed: EC2 deploy `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`, `systemctl is-active stockanalysis-web.service`
- passed: local tunnel `/intelligence` route smoke at `http://127.0.0.1:13000/intelligence` confirmed `오늘의 판단 순서`, `뉴스는 네 단계만 보면 된다`, `오늘의 상위 흐름`, `통과한 AI 근거`, `차단·오염 의심`, `추천 연결`, `차단 목록 보기`, `페이퍼 거래 상태 보기`
- passed: EC2 internal `/intelligence` route smoke at `http://127.0.0.1:3000/intelligence` confirmed the same strings
- passed: Playwright snapshot confirmed the top panel, representative flow, AI candidate, blocked candidate, and recommendation linkage sections.

## Next

- exact next step: 다음 UX slice는 `/data-health` 또는 `/paper-trading` 중 운영자 로그성 문구가 많은 화면을 같은 방식으로 재구성한다.
