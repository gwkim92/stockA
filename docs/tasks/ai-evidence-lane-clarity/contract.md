# Task Contract

## Task

- 이름: ai-evidence-lane-clarity
- 요청: 뉴스 AI 후보, 구조화 결과, 차단 후보 화면에서 사용자가 통과/차단/추천 연결 상태를 바로 이해할 수 있도록 정보 구조와 문구를 정리한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`가 각각 후보 목록, 통과 결과, 추천 입력 제외 항목을 명확히 구분하고, “사람 검토”처럼 실제 기능과 맞지 않는 문구를 제거한다.

## Scope

- 포함:
  - AI evidence lane 간 이동 구조 정리
  - 통과 후보와 차단 후보의 의미를 사용자용 문구로 설명
  - 직접 종목 뉴스, 상위 흐름 뉴스, 뉴스 묶음의 추천 연결 방식을 명확히 표시
  - 화면 문구에서 불필요한 `사람 확인`, `검수`, `검토 가능` 표현 제거
- 제외:
  - DB schema 변경
  - AI extraction runner 변경
  - 추천 점수 산식 변경
  - write API, 승인/반려 저장, 감사 로그 mutation

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-lane-clarity/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - AI extraction runner
  - scheduler configuration

## Verification

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-lane-clarity`
  - EC2 deploy 후 `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked` route smoke

## Done Criteria

- [x] `/ai-evidence`가 후보 목록의 목적과 통과/차단 후속 화면을 명확히 설명한다.
- [x] `/ai-evidence/results`가 직접 종목, 상위 흐름, 뉴스 묶음의 추천 연결 차이를 보여준다.
- [x] `/ai-evidence/blocked`가 차단 이유와 복구 방향을 실패 로그가 아니라 안전장치로 설명한다.
- [x] 불필요한 `사람 확인`, `검수`, `검토 가능` 문구가 제거된다.
- [x] Focused local verification passes.
- [x] EC2 route smoke passes.
