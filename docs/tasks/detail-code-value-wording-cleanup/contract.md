# Task Contract

## Task

- 이름: detail-code-value-wording-cleanup
- 요청: AI 추출 필드와 투자 논리 제목에 남은 코드/내부 표현을 사용자용 한국어 문구로 정리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/ai-evidence/[evidenceId]`의 추출 필드는 `QUANTUM_COMPUTING_POLICY / supportive / ...` 같은 raw 값 대신 테마, 방향, 근거가 분리된 문장으로 보인다.
  - `chunk-news-ai-*` 같은 모델 내부 근거 ID는 사용자용 근거 라벨로 보인다.
  - `QUBT watch thesis via US Market Breadth` 같은 투자 논리 제목은 사용자용 한국어 제목으로 보인다.
  - DB/API/추천 산식/scheduler/broker 로직은 변경하지 않는다.

## Scope

- 포함:
  - AI evidence detail field renderer 개선
  - Korean label normalization 보강
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - live adapter response contract 변경
  - recommendation scoring 변경
  - AI pipeline 재실행
  - broker/order flow 변경

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/detail-code-value-wording-cleanup/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - backend API contract
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Acceptance Criteria

- AI 추출 필드 값에서 주요 코드값이 사람이 읽는 한국어로 보인다.
- AI 추출 필드의 근거 ID가 `chunk-news-ai-*` 원문 그대로 전면 노출되지 않는다.
- 투자 논리 제목의 `watch thesis via ...` 형태가 사용자용 제목으로 보인다.
- Next typecheck/build와 route smoke가 통과한다.

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task detail-code-value-wording-cleanup`
  - EC2 route smoke: `/ai-evidence/ai-evidence-136`, `/stocks/QUBT`, `/theses/thesis-13`
