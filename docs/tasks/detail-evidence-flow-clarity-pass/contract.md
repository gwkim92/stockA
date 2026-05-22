# Task Contract

## Task

- 이름: detail-evidence-flow-clarity-pass
- 요청: 종목 상세, 추천 상세, AI 근거 상세에서 뉴스 -> 상위 흐름 -> 종목 -> 추천 점수 경로를 사용자가 바로 이해하게 한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/stocks/[symbol]`은 직접 뉴스, 상위 흐름, 추천/보유 연결을 먼저 보여준다.
  - `/recommendations/[recommendationId]`는 추천 점수의 입력을 사용자 문장으로 설명하고 내부 용어를 전면에서 줄인다.
  - `/ai-evidence/[evidenceId]`는 AI가 무엇을 분석했고, 왜 종목/테마와 연결됐고, 어디까지 추천 입력인지 명확히 보여준다.
  - API contract, DB schema, 추천 산식, scheduler, broker/order flow는 변경하지 않는다.

## Scope

- 포함:
  - Next.js 상세 화면 문구와 정보 구조 개선
  - 직접 뉴스 / 상위 흐름 / 추천 점수 연결 안내 보강
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - recommendation scoring 변경
  - 뉴스 분류 로직 변경
  - scheduler cadence/activation 변경
  - paper/real order 생성
  - broker/order submission code

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/detail-evidence-flow-clarity-pass/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - backend API contract
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Acceptance Criteria

- 상세 화면 상단에서 사용자가 “무엇을 먼저 봐야 하는지” 알 수 있다.
- `토큰`, `retrieval`, `macro_flow_score`, `preview`, `provenance`, `청크` 같은 개발자 용어가 주요 사용자 문구에서 줄어든다.
- 직접 뉴스와 상위 흐름 전파의 차이가 화면에서 명확하다.
- 추천 상세는 점수 구성요소를 내부 코드보다 사용자 의미로 먼저 설명한다.
- Next typecheck/build와 route smoke가 통과한다.

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task detail-evidence-flow-clarity-pass`
  - EC2 route smoke: `/stocks/QUBT`, `/recommendations/<latest>`, `/ai-evidence/<latest>`
