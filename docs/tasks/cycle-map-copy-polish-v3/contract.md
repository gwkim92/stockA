# cycle-map-copy-polish-v3

## Task Request

- request: `/cycle-map` 화면을 이어서 점검하고 거시→테마→종목 전파 경로를 사용자 관점으로 설명한다.

## Goal

- goal: 흐름 지도 화면을 투자자가 “어떤 뉴스가 어떤 상위 흐름을 만들었는가”, “그 흐름이 어떤 테마와 종목으로 이어졌는가”, “추천 근거로 쓰기 전에 무엇을 더 확인해야 하는가” 순서로 읽게 만든다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `docs/tasks/cycle-map-copy-polish-v3/*`

## Non-Goals

- ontology/graph edge, propagation, cycle snapshot, recommendation scoring logic 변경 금지
- API DTO, DB schema 변경 금지
- broker/order/live trading 변경 금지
- AI extraction, validator logic 변경 금지

## Acceptance Criteria

- `/cycle-map` 주요 문구에 `node`, `thesis`, `validator`, `flag`, `artifact`, `raw`, `runner` 같은 내부/영문 표현이 그대로 보이지 않는다.
- `노드` 중심 표현은 가능한 한 `흐름 항목`, `흐름 단계`, `연결 흐름`처럼 사용자 언어로 바뀐다.
- 전파는 매수 신호가 아니라 상위 흐름이 종목과 추천 검토로 이어지는 근거 후보임을 명확히 한다.
- 기존 링크 구조는 유지한다: 인텔리전스, 추천, 테마 상세, 종목 상세.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cycle-map-copy-polish-v3`
- verification command: EC2 route/content smoke for `/cycle-map`
