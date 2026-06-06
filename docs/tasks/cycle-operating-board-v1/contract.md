# cycle-operating-board-v1

## Request

- request: 사이클 화면을 단순 카드/리스트가 아니라 중장기 투자 판단에 필요한 사이클 운영판으로 개편한다.
- 사용자가 “어느 사이클을 먼저 봐야 하는가”, “왜 이 흐름이 종목과 추천에 연결되는가”, “데이터 공백은 무엇인가”를 바로 알 수 있게 한다.
- 이전에 진행하겠다고 한 `/ai-evidence/[id]`, `/ai-evidence/blocked`, `/ai-evidence/results` 정리 상태도 확인한다.

## Goal

- goal: `/cycle-map`은 우선순위 사이클, 계층별 사이클 레인, 전파 규칙을 보여주고, `/cycles`는 전환·뉴스주도·가격확인·데이터공백 렌즈를 제공한다. 두 화면 모두 매수/매도 신호가 아니라 추천·보유 근거를 점검하는 운영 화면임을 명확히 한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/cycles/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/cycle-operating-board-v1/*`

## Out Of Scope

- 추천 scoring weight 변경
- cycle scoring formula 변경
- DB schema 변경
- scheduler cadence 변경
- portfolio position 변경
- broker/order/write API 변경

## Decisions

- `/cycle-map`은 그래프 노드 나열보다 우선순위 큐를 먼저 보여준다.
- 우선순위는 기존 live DTO의 cycle score, event heat, propagated impact, recommendation linkage, conflict flag만 사용해 화면에서 정렬한다.
- `/cycles`는 상세 목록 위에 네 가지 렌즈를 둔다: 전환, 뉴스 주도, 가격 확인, 데이터 공백.
- AI evidence subroutes는 이번 작업에서 재구현하지 않고 현재 코드/route smoke로 정리 여부를 확인한다.

## Verification Commands

- verification command: `npm run typecheck` in `apps/web`
- verification command: `npm run build` in `apps/web`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-operating-board-v1`
- verification command: route/browser smoke for `/cycle-map`, `/cycles`, `/ai-evidence/results`, `/ai-evidence/blocked`, and one `/ai-evidence/[id]`
