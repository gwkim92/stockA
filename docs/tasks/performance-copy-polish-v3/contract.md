# performance-copy-polish-v3

## Task Request

- request: UX/UI 페이지 순차 점검 흐름에서 `/performance`에 남아 있는 개발자식 용어와 성과 해석 혼선을 줄인다.

## Goal

- goal: 성과 화면을 투자자가 “성과가 충분히 쌓였는가”, “어떤 추천이 맞거나 틀렸는가”, “무엇이 성과에 기여했는가”, “아직 추천 산식이나 주문을 바꾸면 안 되는 이유는 무엇인가” 순서로 읽게 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/performance/page.tsx`
  - `docs/tasks/performance-copy-polish-v3/*`

## Non-Goals

- recommendation scoring weight 변경 금지
- benchmark, portfolio position, outcome record 변경 금지
- broker/order/live trading 활성화 금지
- performance API DTO, DB schema 변경 금지
- calibration 실행 버튼이나 write action 추가 금지

## Acceptance Criteria

- `/performance` 주요 영역에 `weight`, `thesis`, `outcome window`, `quality gate`, `bps` 같은 내부/영문 표현이 그대로 보이지 않는다.
- 성과는 추천 산식 변경이나 주문 실행 근거가 아니라 검증 자료라는 경계가 반복 없이 명확히 보인다.
- 측정된 성과, 품질 평가, 성과 귀속, 커버리지 제외 항목이 한국어 사용자 문장으로 설명된다.
- 기존 추천 링크, 투자 논리 링크, 커버리지/보완 링크는 유지한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-copy-polish-v3`
- verification command: EC2 route/content smoke for `/performance`
