# Session Handoff

## Current Status

- 완료:
  - root cause를 DB에서 확인했다. `ingest.source_document.document_id=22`는 영어 원문이 Dow/Tesla/Iran 뉴스인데 한국어 제목/요약은 SpaceX/Starlink 뉴스로 저장되어 있었다.
  - `stockanalysis.ingest.news.translation`에 번역 grounding validator를 추가했다.
  - validator는 Codex OAuth 번역 결과의 라틴 토큰이 RSS bounded context/source metadata에 없는 경우 source document update 전에 실패시킨다.
  - 오염 사례 회귀 테스트를 추가했다.
  - `/api/dashboard/today`가 EC2 profile scheduler status report를 읽도록 수정했다. 기존 hard-coded `not_installed`는 제거했다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`: passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: failed in local Python 3.14 environment because `fastapi` is missing and Python 3.14 `pyexpat` is broken in this workstation environment.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 841 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-translation-grounding-guard`: passed.

## Exact Next Step

- exact next step: commit/push/deploy하고, EC2에서 `document_id=22` 오염 번역을 정리한 다음 `/api/ai/news-clusters`와 `/api/dashboard/today`를 다시 확인한다.
