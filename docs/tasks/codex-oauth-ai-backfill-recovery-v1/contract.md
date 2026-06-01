# Task Contract

## Task Request

- request: Codex OAuth 장애 기간 동안 실제 AI 번역/구조화/요약/리서치가 누락된 데이터를 찾아 안전하게 다시 실행하고, downstream 근거가 자연스럽게 이어지게 한다.

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - EC2에서 Codex OAuth 실패 기간의 누락/실패 범위가 숫자로 확인되어 있다.
  - OAuth 장애가 아닌 validator false-fail은 재발하지 않도록 테스트와 코드로 보정되어 있다.
  - 뉴스 한국어 번역, 뉴스 AI 구조화, 사이클 요약, 기업 리서치 backfill이 제한 배치로 실행된다.
  - backfill 후 `/api/data-health`가 현재 AI 호출 상태와 남은 누락/실패를 구분해서 보여준다.

## Scope

- 포함:
  - 번역 validator의 과도한 common market/source token 차단 보정
  - 최근 장애 기간의 AI 누락/실패 산정
  - EC2 Codex OAuth backfill smoke와 제한 배치 실행
  - downstream propagation/cycle/research 재연결 상태 확인
  - handoff 갱신
- 제외:
  - 추천 scoring weight 변경
  - benchmark, portfolio position, broker/order flow 변경
  - 실거래 submit
  - 유료 외부 RAG/그래프/vector DB 도입
  - 무제한 전체 재처리

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/translation.py`
  - `tests/test_news_rss_translation.py`
  - `docs/tasks/codex-oauth-ai-backfill-recovery-v1/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB schema/migration
  - 추천 scoring weights
  - broker/order submission code

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation -v`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task codex-oauth-ai-backfill-recovery-v1`
- verification command: EC2 deploy and controlled Codex OAuth backfill smoke

## Done Criteria

- [ ] validator false-fail 테스트가 추가되고 통과한다.
- [ ] EC2에서 제한 배치 backfill이 성공/실패 숫자를 남긴다.
- [ ] 남은 실패가 OAuth 장애인지 데이터 품질 차단인지 구분된다.
- [ ] 추천 weight와 order boundary는 변경되지 않는다.
- [ ] 결과와 남은 위험이 handoff에 기록된다.
