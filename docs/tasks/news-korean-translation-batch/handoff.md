# Session Handoff

## Active Task

- 이름: news-korean-translation-batch
- 담당: Codex
- 날짜: 2026-05-23

## Current Status

- 완료:
  - task contract, handoff, review 문서를 생성했다.
  - 아래 구현 항목을 완료했고 로컬 검증은 통과했다.
- 막힌 점:
  - 없음.
- 아직 하지 않은 것:
  - EC2 Postgres migration 적용과 실제 Codex OAuth translation batch 실행은 다음 단계다.

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

## Remaining Runtime Work

- Apply migration `0016_news_document_translation.sql` to EC2 Postgres.
- Run a small EC2 Codex OAuth translation batch.
- Re-run news cluster evidence so `/intelligence` and `/ai-evidence/...` show persisted translations instead of fallback labels.

## Exact Next Step

- 다음 세션은 이것부터 시작: EC2 `/opt/stockanalysis/app`에 최신 코드를 배포한 뒤 `db/migrations/0016_news_document_translation.sql`을 적용하고, `news-rss-translation-run --limit 3 --provider codex_oauth --execute`를 실행해 `ingest.source_document`에 실제 `korean_title`, `korean_summary`, `translation_confidence`가 저장되는지 확인한다.
