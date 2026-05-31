# paper-trading-status-clarity-ux-v3

## Task Request

- request: 추천 상세에서 이어지는 `/paper-trading` 화면을 사용자가 이해할 수 있게 정리한다.

## Goal

- goal: 가상 매매 화면에서 `실제 주문 여부 -> 가상 후보 여부 -> 차단 조건 -> 위험 예산 연결 -> 후보별 근거`를 명확히 보여주고, 내부 로그성 표현을 줄인다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `docs/tasks/paper-trading-status-clarity-ux-v3/*`

## Non-Goals

- 가상 매매 후보 계산, 포트폴리오 위험 예산, 추천 산식, DB/API, scheduler, AI batch는 변경하지 않는다.
- 실거래 주문, 쓰기 API, broker submit, 사용자 입력 버튼은 추가하지 않는다.
- 기존 `getPaperTradingPreview`, `getTradingReadiness` DTO contract를 변경하지 않는다.

## Acceptance Criteria

- `/paper-trading`에서 현재가 실제 주문 상태인지, 가상 매매 후보 상태인지, 차단 상태인지 바로 구분된다.
- `페이퍼`, `주문 경계`, `eval_run_id`, `active share`, `order_boundary`, `broker submit` 같은 내부 표현이 주요 사용자 문구로 노출되지 않는다.
- 실제 주문 0건, 가상 후보 수, 차단 조건, 위험 예산 연결, 후보별 추천/현재비중/목표비중이 한 흐름으로 읽힌다.
- 실거래 차단과 주문 불가 상태는 숨기지 않고 사용자용 한국어로 표시한다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route/content smoke와 Playwright snapshot으로 핵심 문구를 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/paper-trading`
- verification command: Playwright snapshot for `http://127.0.0.1:13000/paper-trading`

## Boundaries

- 추천 산식과 투자 결과는 변경하지 않는다.
- 실거래 금지, 위험 예산 차단, 후보 없음 같은 상태는 낮춰 보이지 않게 유지한다.
- 이번 작업은 UX/copy visibility slice다.
