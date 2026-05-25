# Session Handoff

## Current Status

- 완료:
  - root cause를 DB에서 확인했다. `ingest.source_document.document_id=22`는 영어 원문이 Dow/Tesla/Iran 뉴스인데 한국어 제목/요약은 SpaceX/Starlink 뉴스로 저장되어 있었다.
  - `stockanalysis.ingest.news.translation`에 번역 grounding validator를 추가했다.
  - validator는 Codex OAuth 번역 결과의 라틴 토큰이 RSS bounded context/source metadata에 없는 경우 source document update 전에 실패시킨다.
  - 오염 사례 회귀 테스트를 추가했다.
  - `/api/dashboard/today`가 EC2 profile scheduler status report를 읽도록 수정했다. 기존 hard-coded `not_installed`는 제거했다.
  - EC2 `/opt/stockanalysis/app`를 `1cbee92`로 fast-forward 배포했다.
  - EC2에서 `document_id=22`를 Codex OAuth로 재번역했다: `run_id=724`, `invocation_id=1017`.
	  - EC2에서 `news-rss-cluster-evidence-run --as-of-date 2026-05-25 --event-limit 120 --max-clusters 30`를 실행해 최신 cluster artifact를 만들었다: `run_id=725`, MACRO_RATES_FED artifact `358`.
	  - EC2 `/api/dashboard/today`는 `scheduler=installed`를 반환한다.
	  - EC2 `/api/ai/news-clusters?limit=1`과 브라우저 `/ai-evidence/ai-evidence-358`에서 SpaceX/Starlink 오염 제목이 사라지고 Dow/Tesla/Iran 원문과 한국어 번역이 일치함을 확인했다.
  - EC2 RSS 번역 원장 279건을 historical grounding scan으로 확인했다.
  - 1차 validator flag는 71건이었지만 대부분 `Yahoo Finance`, `MarketWatch`, `AI`, `ETF` 같은 출처/일반 약어였다.
  - 2차 material filter에서 고위험 오염 후보 9건을 분리했고, alias 수준 5건을 제외한 4건(`document_id=56,114,712,900`)을 Codex OAuth로 재번역했다: `run_id=726`, `invocation_id=1048..1051`.
  - 재스캔 결과 고위험 4건은 해소됐고 남은 5건은 `Musk→Elon`, `Dimon→Jamie`, `PANW→Palo Alto Networks` alias 확장으로 판단해 삭제하지 않았다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`: passed.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: failed in local Python 3.14 environment because `fastapi` is missing and Python 3.14 `pyexpat` is broken in this workstation environment.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: passed, 841 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m compileall -q src tests`: passed.
- `git diff --check`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-translation-grounding-guard`: passed.
- EC2 targeted tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_news_rss_translation tests.test_frontend_live_adapter -v`: passed.
- EC2 compile: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`: passed.
- EC2 services: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`: active after restart.
- Local tunnel smoke: `http://127.0.0.1:13000/`: HTTP 200, `http://127.0.0.1:18787/__health`: ok.
- Browser smoke: `/ai-evidence/ai-evidence-358` shows corrected Korean translation and no old SpaceX/Starlink mismatch.
- Historical scan: translated RSS documents 279건 검사, 고위험 재번역 4건 완료, 재스캔 후 남은 material suspects 5건은 alias 확장으로 보류.

## Exact Next Step

- exact next step: recommendation outcome 표본을 쌓을 수 있도록 market daily와 decision daily가 충분히 누적되는지 점검하고, `recommendation-quality-eval-run` 결과가 `needs_more_data`에서 벗어날 때까지 추천 weight 변경을 계속 금지한다. 단, 사용자 화면의 “validator/검토” 표현은 별도 UX 정리 대상으로 남아 있다.
