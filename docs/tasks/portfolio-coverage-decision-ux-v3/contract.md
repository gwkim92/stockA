# portfolio-coverage-decision-ux-v3

## Task Request

- request: 추천 상세와 가상 매매 화면에서 이어지는 `/portfolio/coverage`를 사용자 관점으로 정리한다.

## Goal

- goal: 포트폴리오 화면에서 `보유 상태 -> 투자 논리/성과 연결 -> 위험 예산 -> 리밸런싱 검토 후보 -> 성과 성숙 대기 -> 실거래 차단`을 명확히 보여준다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `docs/tasks/portfolio-coverage-decision-ux-v3/*`

## Non-Goals

- 보유 비중, 포트폴리오 위험 예산 계산, 추천 산식, benchmark definition, DB/API, scheduler, AI batch는 변경하지 않는다.
- 실거래 주문, 쓰기 API, broker submit, 사용자 입력 버튼은 추가하지 않는다.
- 기존 `getPortfolioCoverage`, `getTradingReadiness` DTO contract를 변경하지 않는다.

## Acceptance Criteria

- `/portfolio/coverage`에서 지금 무엇을 봐야 하는지, 무엇이 아직 대기/차단인지 먼저 보인다.
- `주문 경계`, `eval_run_id`, `active share`, `drift`, `broker submit`, `가중치` 같은 내부 표현이 주요 사용자 문구로 노출되지 않는다.
- 보유 종목, 위험 예산, 리밸런싱 후보, 포지션 크기 후보, 성과 성숙 대기, 실행 라우터가 사용자용 한국어로 보인다.
- 실거래 차단과 추천 산식 변경 금지는 숨기지 않고 사용자용 한국어로 표시한다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route/content smoke와 Playwright snapshot으로 핵심 문구를 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/portfolio/coverage`
- verification command: Playwright snapshot for `http://127.0.0.1:13000/portfolio/coverage`

## Boundaries

- 추천 산식과 투자 결과는 변경하지 않는다.
- 실거래 금지, 위험 예산 차단, 성과 성숙 대기는 낮춰 보이지 않게 유지한다.
- 이번 작업은 UX/copy visibility slice다.
