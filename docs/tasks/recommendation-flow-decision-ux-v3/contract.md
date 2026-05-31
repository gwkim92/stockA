# recommendation-flow-decision-ux-v3

## Task Request

- request: 추천 목록과 추천 상세 화면을 사용자 관점으로 다시 정리한다.

## Goal

- goal: 추천 화면을 `후보 확인 -> 사용 가능 범위 -> 근거 경로 -> 재무/밸류에이션 -> 가상 매매/실거래 차단` 순서로 읽게 만들고, 내부 코드명과 개발자 로그성 문구를 줄인다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/components/professional-research-flow.tsx`
  - `docs/tasks/recommendation-flow-decision-ux-v3/*`

## Non-Goals

- 추천 점수, weight, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- DB schema, FastAPI DTO, scheduler, AI batch, ingest 로직은 변경하지 않는다.
- 실거래 주문, 쓰기 API, 사용자 입력 검토 버튼은 추가하지 않는다.

## Acceptance Criteria

- `/recommendations`에서 추천 후보가 주문 화면이 아니라 중장기 검토 후보임을 분명히 알 수 있다.
- `/recommendations/[id]`에서 `paper validation`, `broker`, `source_run_id`, raw score component name, `source blocker`, `DCF-lite` 같은 내부 표현이 주요 문구로 노출되지 않는다.
- 추천 상세는 `현재 결론`, `근거 경로`, `재무/밸류에이션`, `가상 매매`, `실거래 차단`을 사용자가 따라 읽을 수 있게 한다.
- 경고, 원천 한계, 차단, 실거래 금지는 숨기지 않고 사용자용 한국어로 표시한다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route smoke에서 `/recommendations`, `/recommendations/recommendation-67`, `/recommendations/recommendation-157`이 200을 반환한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-flow-decision-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/recommendations`, `/recommendations/recommendation-67`, `/recommendations/recommendation-157`

## Boundaries

- 추천 산식과 투자 결과는 변경하지 않는다.
- 차단 상태와 원천 부족 상태는 낮춰 보이지 않게 유지한다.
- 이번 작업은 UX/copy visibility slice다.
