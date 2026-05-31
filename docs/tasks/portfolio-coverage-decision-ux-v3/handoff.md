# portfolio-coverage-decision-ux-v3 Handoff

## Status

- completed: `/portfolio/coverage` 화면의 보유 검토, 위험 예산, 리밸런싱 후보, 성과 성숙 대기 문구를 사용자용 한국어로 정리했고 EC2/Playwright smoke까지 확인했다.

## Completed

- completed: task contract를 생성했다.
- completed: `/portfolio/coverage`의 제목을 `보유 검토`로 바꾸고, 내부 표현을 사용자 판단 흐름으로 정리했다.
- completed: `주문 경계`, `eval_run_id`, `threshold`, `가중치`, `페이퍼 검증` 같은 주요 개발자용 표현을 화면 라벨에서 숨기고 `실거래 상태`, `검증 기록`, `검토 기준`, `추천 산식 반영 비중`, `가상 매매 검증`으로 바꿨다.
- completed: EC2 `stockanalysis-web.service`에 배포했고 `/portfolio/coverage`가 `200`으로 응답한다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-ux-v3`
- passed: `git diff --check`
- passed: EC2 deploy and route/content smoke. Required terms `보유 검토`, `보유 검토 지도`, `실거래 상태`, `가상 매매 검증`, `성과 성숙 대기`, `리밸런싱 후보`, `추천 산식 반영 비중` present.
- passed: Playwright snapshot for `http://127.0.0.1:13000/portfolio/coverage`; required terms present and visible forbidden terms `주문 경계`, `eval_run_id`, `active share`, `broker submit`, `페이퍼 검증`, `threshold`, `가상 거래` absent.

## Exact Next Step

- exact next step: 다음 화면 `/data-health` 또는 `/trading-readiness`를 같은 방식으로 사용자용 문구와 판단 흐름 기준으로 정리한다.
