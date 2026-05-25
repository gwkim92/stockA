# Task Contract

## Task

- 이름: news-translation-grounding-guard
- 요청: EC2 라이브 화면에서 확인된 원문 뉴스 제목과 저장 한국어 제목 불일치 데이터 오염을 차단하고 정리한다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `news-rss-korean-translation` 배치가 원문 bounded context에 없는 영어 고유명사/티커/회사명/제품명을 번역 결과에 새로 만들면 source document 업데이트를 차단하고 실패 기록을 남긴다.

## Scope

- 포함:
  - Codex OAuth 뉴스 번역 결과 grounding validator
  - 오염 사례 회귀 테스트
  - EC2 dashboard scheduler status hard-code 제거
  - task handoff/review 문서
  - 확인된 EC2 오염 문서 정리
- 제외:
  - 유료 번역 API 도입
  - 추천 점수 산식 변경
  - broker/order/live trading 변경
  - 전체 뉴스 번역 평가 체계 재설계

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/translation.py`
  - `tests/test_news_rss_translation.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/news-translation-grounding-guard/*`
- 수정 금지 파일:
  - `.env` secret values
  - recommendation scoring weights
  - broker/order submit path
  - scheduler cadence/timer units

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-translation-grounding-guard`

## Done Criteria

- 원문에 없는 `SpaceX`, `Starlink`, `IPO` 같은 영어 엔티티가 번역 결과에 들어오면 저장 전 실패한다.
- 실패는 성공 invocation/update로 기록되지 않는다.
- `/api/dashboard/today`는 EC2 profile scheduler status report가 installed이면 `scheduler=installed`를 반환한다.
- EC2의 확인된 오염 번역값은 삭제 또는 재번역되어 화면에 잘못 노출되지 않는다.
