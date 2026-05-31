# cycles-copy-polish-v3

## Task Request

- request: `/cycles` 화면을 이어서 점검하고, 사이클 상태·근거·추천 영향 문구를 사용자 관점으로 정리한다.

## Goal

- goal: 사이클 화면을 투자자가 “어떤 테마가 어떤 단계인가”, “무슨 근거 축이 강한가”, “추천/보유 투자 논리와 충돌하는가”, “원인 경로는 어디서 확인하는가” 순서로 읽게 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycles/page.tsx`
  - `docs/tasks/cycles-copy-polish-v3/*`

## Non-Goals

- cycle snapshot calculation, feature scoring, propagation logic 변경 금지
- recommendation scoring weight 변경 금지
- benchmark, portfolio position, broker/order/live trading 변경 금지
- API DTO, DB schema 변경 금지

## Acceptance Criteria

- `/cycles` 주요 문구에 `thesis`, `runner`, `artifact`, `raw`, `source` 같은 내부/영문 표현이 그대로 보이지 않는다.
- 첫 화면에서 사이클은 매수 신호가 아니라 투자 논리 점검 출발점이라는 경계가 명확하다.
- 상태표의 근거 축은 뉴스 흐름, 가격 흐름, 기업 품질로 읽힌다.
- 원인 경로는 `/cycle-map`과 테마 상세로 이어진다는 다음 행동이 보인다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycles-copy-polish-v3`
- verification command: EC2 route/content smoke for `/cycles`
