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
  - EC2 system services `stockanalysis-frontend-api.service`, `stockanalysis-web.service`를 system scope에서 재시작했고 둘 다 active 상태다.
  - 로컬 SSH tunnel `http://127.0.0.1:13000`에서 source document 화면이 persisted Korean translation을 표시하는 것을 Playwright snapshot으로 확인했다.
- 막힌 점:
  - 없음.
- 아직 하지 않은 것:
  - 남은 untranslated RSS 문서를 전량 번역하려면 운영 배치가 다음 주기에서 계속 실행되어야 한다.

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
- Stored DB sample:
  - document `832`
  - `korean_title`: `영화관 사업이 쇠퇴하는 가운데 흐름을 거스른 IMAX, 잠재 인수자들에게 매력적인 이유`
  - `translation_confidence`: `0.8600`
  - `translation_provider`: `codex_oauth`
- EC2 cluster regeneration: `run_id=519`, inserted artifacts `252`, `253`, `254`, `255`.
- `/api/data-health`: `news-korean-translation-intraday succeeded pipeline-run-518 ok`, `event-intelligence-weekly succeeded pipeline-run-519 ok`.
- Playwright screenshot: `/private/tmp/stockanalysis-runtime/news-korean-translation-source-document.png`.

## Exact Next Step

- 다음 세션은 이것부터 시작: `news-rss-translation-run --limit 20 --provider codex_oauth --execute`를 운영 주기에서 반복 실행해 아직 번역되지 않은 RSS 문서 수를 줄이고, `/intelligence`와 `/ai-evidence/...`에서 오래된 artifact가 아닌 최신 번역 포함 artifact가 우선 노출되는지 점검한다.
