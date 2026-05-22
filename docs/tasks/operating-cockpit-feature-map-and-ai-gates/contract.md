# Task Contract

## Task

- 이름: operating-cockpit-feature-map-and-ai-gates
- 요청: 서비스 전체 기능 12개가 어디서 보이는지 명확히 만들고, 뉴스 AI validator 차단/통과 흐름을 화면에서 확인 가능하게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 홈에서 데이터 수집, 뉴스 원장, 1차 분류, Codex OAuth 분석, 구조화 결과, validator 차단/통과, 추천 연결, AI 상세, 추천 신호, thesis, paper 거래 위치가 보인다.
  - 데이터 수집 화면에서 수집/분석 작업별 상태와 사용처가 먼저 보인다.
  - 뉴스/AI 화면에서 원문 수집, 1차 분류, Codex OAuth 분석, 검증, 추천 연결 순서가 보인다.
  - validator rejected 또는 low-signal 보류 후보를 AI 근거 화면에서 목록으로 볼 수 있다.
  - DB schema, 추천 산식, scheduler cadence, secrets는 변경하지 않는다.

## Scope

- 포함:
  - `/` 기능 지도 보강
  - `/data-health` 수집/분석별 상태 요약 보강
  - `/intelligence` 뉴스 처리 흐름 보강
  - `/ai-evidence` 통과/차단 후보 목록 보강
  - `/paper-trading` 실제 주문 여부와 paper 단계 표시 보강
  - `/api/events` read-only filter 확장
- 제외:
  - DB schema 변경
  - 추천 점수 산식 변경
  - 실거래 주문 제출
  - 외부 RAG/vector DB 도입
  - paid provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/globals.css`
  - `apps/web/src/lib/korean-labels.ts`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/operating-cockpit-feature-map-and-ai-gates/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - scheduler cadence/profile definitions
  - recommendation scoring logic
  - broker/live order submit logic

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task operating-cockpit-feature-map-and-ai-gates`

## Done Criteria

- [ ] 홈에서 12개 기능 위치가 보인다.
- [ ] 데이터 수집 화면이 작업별 상태를 먼저 보여준다.
- [ ] 뉴스/AI 화면이 분석 순서를 먼저 보여준다.
- [ ] AI 근거 화면이 통과/차단/보류 후보를 분리한다.
- [ ] paper 화면이 실제 주문 여부를 명확히 보여준다.
- [ ] 로컬 검증이 통과한다.
