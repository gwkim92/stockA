# portfolio-coverage-decision-ux-v3 Handoff

## Status

- in_progress: `/portfolio/coverage` 화면의 보유 검토, 위험 예산, 리밸런싱 후보, 성과 성숙 대기 문구를 사용자용 한국어로 정리했고 EC2 smoke 전이다.

## Completed

- completed: task contract를 생성했다.
- completed: `/portfolio/coverage`의 제목을 `보유 검토`로 바꾸고, 내부 표현을 사용자 판단 흐름으로 정리했다.
- completed: `주문 경계`, `eval_run_id`, `threshold`, `가중치`, `페이퍼 검증` 같은 주요 개발자용 표현을 화면 라벨에서 숨기고 `실거래 상태`, `검증 기록`, `검토 기준`, `추천 산식 반영 비중`, `가상 매매 검증`으로 바꿨다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-ux-v3`
- passed: `git diff --check`
- pending: EC2 deploy and route/content smoke.
- pending: Playwright snapshot.

## Exact Next Step

- exact next step: 변경분을 커밋·푸시하고 EC2 배포, route/content smoke, Playwright snapshot을 수행한다.
