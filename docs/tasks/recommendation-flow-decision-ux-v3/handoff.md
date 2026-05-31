# recommendation-flow-decision-ux-v3 Handoff

## Status

- completed: 추천 목록과 추천 상세의 사용자 문구, 라벨, 읽기 흐름을 정리하고 EC2 반영·route smoke·Playwright snapshot 검증까지 완료했다.

## Completed

- completed: task contract를 생성했다.
- completed: `/recommendations` hero, 판정 카드, 추천 목록에서 `페이퍼`, `broker flow`, `AI/이벤트`, `주문 경계` 같은 내부 표현을 사용자용 한국어로 바꿨다.
- completed: `/recommendations/[recommendationId]`에 표시 치환 helper를 추가해 score component, source type, order boundary, 원천 차단, 가상 매매, 밸류에이션 관련 내부 표현을 정리했다.
- completed: 추천 상세의 주요 흐름을 `현재 판단 -> 추천 사용 가능 범위 -> 거시/테마/기업/재무/밸류에이션/리스크/가상 매매 -> 근거 경로 -> 점수 입력` 순서로 읽히게 정리했다.
- completed: `ProfessionalResearchFlow`의 차단 문구를 가상 매매 검증/실거래 입력 기준으로 바꿨다.
- completed: 추천 산식, DB/API, scheduler, AI batch, 포트폴리오, broker/order flow는 변경하지 않았다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-flow-decision-ux-v3`
- passed: `git diff --check`
- passed: commits `43a99980`, `e9929e90`, `04f9627e` pushed to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- passed: EC2 `git pull --ff-only`, Next typecheck/build, and `stockanalysis-web.service` restart returned `active`.
- passed: EC2 route/content smoke for `/recommendations`, `/recommendations/recommendation-189`, `/recommendations/recommendation-67` returned 200 and required terms were present.
- passed: Playwright snapshot for `http://127.0.0.1:13000/recommendations` confirmed `추천 신호를 보고`, `가상 매매`, `뉴스·AI 해석`, `실거래 차단 상태`.
- passed: Playwright snapshot for `http://127.0.0.1:13000/recommendations/recommendation-189` confirmed `추천 사용 가능 범위`, `가상 매매 검증`, `실거래 상태`, `뉴스·AI 해석`, `상위 흐름`, and no targeted visible `DCF-lite`, `paper validation`, `broker flow`, `source blocker`, `현재 총점 미반영`, `거래 경계`.

## Exact Next Step

- exact next step: continue page-by-page UX refactor with `/portfolio/coverage` or `/paper-trading`, because 추천 상세에서 사용자가 다음으로 이동하는 검토/가상 매매 화면의 문구와 구조가 아직 같은 수준으로 정리되지 않았다.
