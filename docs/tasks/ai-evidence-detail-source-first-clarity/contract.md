# Task Contract

## Task

- 이름: ai-evidence-detail-source-first-clarity
- 요청: `/ai-evidence/[id]` 상세 화면에서 사용자가 먼저 봐야 할 원천 뉴스, AI 자동 판정, 종목/테마 연결 경로가 한눈에 보이도록 정보 구조와 문구를 정리한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: AI 근거 상세 첫 화면에서 한국어 원천 뉴스, AI 자동 판정, 읽기 전용 운영 경계, 종목/추천 연결 경로를 바로 이해할 수 있다.

## Scope

- 포함:
  - AI 근거 품질 카드 문구를 `AI 자동 판정` 중심으로 정리
  - 원천 뉴스 한국어 제목/요약 preview를 상단에 추가
  - `검토 저장/저장 버튼 없음/사람이 봐야 함` 같은 부정확하거나 불필요한 문구 제거
  - 기존 DTO와 `NewsTitleBlock` 재사용
- 제외:
  - 새 AI 호출
  - DB schema 변경
  - 추천 점수 산식 변경
  - write API, 승인/반려 저장, 감사 로그 mutation

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `docs/tasks/ai-evidence-detail-source-first-clarity/*`
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
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-evidence-detail-source-first-clarity`
  - EC2 deploy 후 `/ai-evidence/[id]` route smoke

## Done Criteria

- [x] `/ai-evidence/[id]` 상단에 한국어 원천 뉴스 preview가 보인다.
- [x] `AI 자동 판정` 카드가 근거 상태를 명확히 설명한다.
- [x] 불필요한 `저장 버튼 없음`, `사람이 봐야 함` 문구가 제거된다.
- [x] Focused local verification passes.
- [ ] EC2 route smoke passes.
