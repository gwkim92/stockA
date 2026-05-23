# Session Handoff

## Active Task

- 이름: news-korean-translation-batch
- 담당: Codex
- 날짜: 2026-05-23

## Current Status

- 완료:
  - task contract, handoff, review 문서를 생성했다.
  - 아래 구현 항목을 완료했고 로컬 검증은 통과했다.
  - GitHub branch `codex/local-mvp-runtime-aws-bootstrap`에 commit `9b8c7d2`를 push했다.
  - EC2 `/opt/stockanalysis/app`를 `9b8c7d2`로 fast-forward 배포했다.
  - EC2 Postgres에 `0016_news_document_translation.sql` migration을 적용했다.
  - EC2에서 `news-rss-translation-run --as-of-date 2026-05-23 --limit 3 --provider codex_oauth --execute`를 실행했고 3건 모두 번역 저장에 성공했다.
  - EC2에서 `news-rss-cluster-evidence-run --as-of-date 2026-05-23`를 재실행했고 새 cluster artifact 4건을 생성했다.
  - EC2에서 추가 번역 배치 3회를 실행했다.
    - `run_id=520`: 20건 업데이트, 실패 0건.
    - `run_id=521`: 50건 업데이트, 실패 0건.
    - `run_id=523`: 50건 업데이트, 실패 0건.
  - EC2에서 남은 번역 대기분을 추가로 전량 처리했다.
    - `run_id=525`: 50건 업데이트, 실패 0건.
    - `run_id=526`: 50건 업데이트, 실패 0건.
    - `run_id=527`: 13건 업데이트, 실패 0건.
  - EC2에서 최신 번역 반영 후 `news-rss-cluster-evidence-run --as-of-date 2026-05-23 --event-limit 100 --max-clusters 4`를 재실행했고 `run_id=524`, artifact `260..263`을 생성했다.
  - EC2에서 전체 뉴스 묶음 갱신을 위해 `news-rss-cluster-evidence-run --as-of-date 2026-05-23 --event-limit 500 --max-clusters 20`을 실행했고 `run_id=529`, artifact 19건을 추가 생성했다.
  - EC2 RSS source document 상태는 총 236건 중 236건 번역 완료, 0건 대기다.
  - 최신 `/api/ai/news-clusters?asOfDate=2026-05-23&limit=20`는 20개 cluster의 대표 이벤트/source documents가 모두 저장 한국어 번역을 포함한다.
  - `ai evidence neighborhood` SQL/DTO가 원천 문서 번역 필드를 누락해 하단 “최근 관련 이벤트”가 fallback으로 보이던 문제를 수정했다.
  - EC2 system services `stockanalysis-frontend-api.service`, `stockanalysis-web.service`를 system scope에서 재시작했고 둘 다 active 상태다.
  - 로컬 SSH tunnel `http://127.0.0.1:13000`에서 source document 화면이 persisted Korean translation을 표시하는 것을 Playwright snapshot으로 확인했다.
- 막힌 점:
  - 없음.
- 아직 하지 않은 것:
  - 새로 수집되는 RSS 문서는 다음 운영 주기에서 계속 번역되어야 한다.

## Implemented

- Added migration `0016_news_document_translation.sql`.
  - `ingest.source_document.korean_title`
  - `ingest.source_document.korean_summary`
  - `ingest.source_document.translation_confidence`
  - provider/model/invocation trace fields and pending translation indexes.
- Added `stockanalysis.ingest.news.translation`.
  - Offline `codex_oauth` translation batch.
  - `fixture` provider support for tests.
  - `ai.model_invocation` audit row per translated document.
  - `source_document` translation update after successful invocation.
- Added operations CLI:
  - `stockanalysis-operations news-rss-translation-run --as-of-date YYYY-MM-DD --limit 20 --provider codex_oauth --execute`.
- Added `news-korean-translation` to the `news-intraday` operating-data profile before cluster evidence and AI evidence.
- Added data-health cadence entry `news-korean-translation-intraday`.
- Updated cluster evidence output/request hash to carry persisted Korean translations into newly generated cluster artifacts.
- Updated frontend DTOs and pages to prefer DB translations over heuristic Korean labels.
- Updated AI evidence neighborhood SQL/DTO/story-group rendering to pass DB translations into related event/story cards.

## Runtime Notes

- FastAPI/web requests remain read-only and do not call Codex OAuth.
- Codex OAuth is only invoked by the offline batch runner.
- Existing cluster artifacts created before this task will not contain translation fields. Re-running `news-rss-translation-run --execute` followed by `news-rss-cluster-evidence-run` creates new cluster artifacts with Korean title/summary fields because the cluster request hash now includes translation payload content/version.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_translation tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_frontend_live_adapter tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`

## Runtime Evidence

- EC2 translation run: `run_id=518`, `updated_document_count=3`, `failed_document_count=0`.
- EC2 additional translation runs:
  - `run_id=520`, `updated_document_count=20`, `failed_document_count=0`.
  - `run_id=521`, `updated_document_count=50`, `failed_document_count=0`.
  - `run_id=523`, `updated_document_count=50`, `failed_document_count=0`.
  - `run_id=525`, `updated_document_count=50`, `failed_document_count=0`.
  - `run_id=526`, `updated_document_count=50`, `failed_document_count=0`.
  - `run_id=527`, `updated_document_count=13`, `failed_document_count=0`.
- EC2 translation coverage: RSS source documents `translated=236`, `pending=0`, `total=236`.
- Stored DB sample:
  - document `832`
  - `korean_title`: `영화관 사업이 쇠퇴하는 가운데 흐름을 거스른 IMAX, 잠재 인수자들에게 매력적인 이유`
  - `translation_confidence`: `0.8600`
  - `translation_provider`: `codex_oauth`
- EC2 cluster regeneration: `run_id=519`, inserted artifacts `252`, `253`, `254`, `255`.
- EC2 latest cluster regeneration: `run_id=524`, inserted artifacts `260`, `261`, `262`, `263`.
  - `ai-evidence-260`: rates/Fed, 10/10 events translated.
  - `ai-evidence-261`: energy/geopolitics, 10/10 events translated.
  - `ai-evidence-262`: AI semiconductor, 9/9 events translated.
  - `ai-evidence-263`: quantum computing policy, 3/3 events translated and linked to `QUBT`.
- EC2 full cluster regeneration: `run_id=529`, requested 193 events, produced 20 clusters, inserted 19 artifacts, skipped 1 existing, failed 0.
- FastAPI verification: `/api/ai/news-clusters?asOfDate=2026-05-23&limit=20` returned `cluster_count=20`, `all_source_documents_translated=true`, `all_events_translated=true`.
- `/api/data-health`: `news-korean-translation-intraday succeeded pipeline-run-518 ok`, `event-intelligence-weekly succeeded pipeline-run-519 ok`.
- Playwright screenshot: `/private/tmp/stockanalysis-runtime/news-korean-translation-source-document.png`.
- Playwright snapshot: `http://127.0.0.1:13000/ai-evidence/ai-evidence-263` shows the three representative quantum news items as `한국어 번역` with confidence values.

## Exact Next Step

- 다음 세션은 이것부터 시작: 새 RSS 수집분이 들어온 뒤 `news-rss-translation-run`이 자동 주기에서 실행되는지 `/data-health`와 `ops.pipeline_run`으로 확인한다. 그 다음 화면 QA는 `/intelligence`, `/ai-evidence/...`, `/stocks/{symbol}`의 문구/레이아웃 정리로 이어간다.
