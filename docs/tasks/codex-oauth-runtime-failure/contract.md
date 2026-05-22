# Task Contract

## Task

- 이름: codex-oauth-runtime-failure
- 요청: EC2에서 최근 `codex_oauth` 뉴스 후보 분석이 실패하는 원인을 확인하고, 가능한 경우 근본 수정한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 최근 `codex_oauth` 실패가 인증, 모델, CLI 옵션, 출력 schema, runner 코드 중 어디서 발생하는지 확인한다.
  - 수정이 코드로 가능하면 테스트를 추가하고 배포한다.
  - 운영 환경 조치가 필요하면 정확한 명령/설정과 검증 방법을 남긴다.

## Scope

- 포함:
  - EC2 `codex exec` 최소 재현
  - `news-rss-ai-extract-run` 호출 경로 조사
  - 원인별 최소 수정
  - task handoff와 검증 기록
- 제외:
  - 유료 API key 도입
  - OpenAI 계정/브라우저 OAuth 재로그인 수동 수행
  - 뉴스 추천 점수 산식 변경
  - DB schema 변경
  - scheduler 주기 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `tests/test_news_rss_ai_extract.py`
  - `docs/tasks/codex-oauth-runtime-failure/*`
- 수정 금지 파일:
  - `.env` secret values
  - EC2 secret env 파일 내용 출력
  - DB migrations/schema
  - scheduler units/timers
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - EC2 safe env/CLI diagnostics without printing secrets
  - EC2 minimal `codex exec` reproduction
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task codex-oauth-runtime-failure`

## Done Criteria

- [x] Root cause is identified with EC2 evidence.
- [x] Code/config fix is applied if this repo can fix it.
- [x] `codex_oauth` smoke either succeeds or the external blocker is documented precisely.
- [x] Local verification and AWH pass.
- [x] Handoff documents the next exact step.
