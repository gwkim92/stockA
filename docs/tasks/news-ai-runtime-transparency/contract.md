# Task Contract

## Task

- 이름: news-ai-runtime-transparency
- 요청: 뉴스 분석이 실제로 무엇을 분석하고, LLM을 쓰는지, 왜 영어가 보이는지 화면과 보고에서 명확히 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai/news-clusters` summary가 LLM 후보 분석 성공/실패 수와 로컬 규칙 묶음 수를 분리해서 반환한다.
  - `/intelligence`가 뉴스 묶음과 개별 LLM 후보 분석을 같은 “AI 성공”처럼 표시하지 않는다.
  - 화면에 영어가 남는 이유가 RSS 원문/로컬 규칙 키워드/LLM 한국어 출력의 차이로 설명된다.

## Scope

- 포함:
  - AI 뉴스 클러스터 API summary 확장
  - `/intelligence` 운영 상태/문구 개선
  - 타입과 regression test 갱신
  - task handoff 갱신
- 제외:
  - DB migration
  - 스케줄러 주기 변경
  - LLM provider 인증 수정
  - 추천 점수 산식 변경
  - 유료 번역/뉴스 API 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/tasks/news-ai-runtime-transparency/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-runtime-transparency`
  - EC2 API/browser smoke for `/api/ai/news-clusters` and `/intelligence`

## Done Criteria

- [x] API summary exposes LLM candidate success/failure counts.
- [x] UI distinguishes LLM candidate extraction from local rule cluster evidence.
- [x] UI explains why English source/story text can remain visible.
- [x] Local verification and AWH pass.
- [ ] EC2 deploy and browser smoke pass.
