# Session Handoff

## Active Task

- 이름: news-ai-evidence-quality-pipeline
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 완료:
  - task contract, handoff, review 문서를 생성했다.
  - news AI extraction runner를 추가했다.
  - `stockanalysis-operations news-rss-ai-extract-run` CLI를 추가했다.
  - event-intelligence job command references를 새 runner로 전환했다.
  - fixture 기반 unit tests와 verify script를 추가했다.
  - AI candidate 실패가 service/timer 실패로 번지지 않도록 operations CLI는 `completed_with_fallback`도 exit 0으로 처리한다.
  - `news_event_candidate` artifact에 `extracted_fields`를 함께 저장해 기존 AI 근거 상세 화면이 뉴스 요약, 테마 영향, 종목 영향, 불확실성을 표시할 수 있게 했다.
  - `/data-health`의 AI evidence 설명 문구를 Codex OAuth batch + validator 흐름으로 바꿨다.
  - Python 3.13 검증 venv에서 전체 unit test와 Next typecheck/build가 통과했다.
  - GitHub 최신 코드(`bd29893`)를 EC2 `/opt/stockanalysis/app`에 배포했다.
  - EC2 Postgres의 기존 application schema를 삭제하고 migrations/seeds를 재적용한 뒤 full-recovery profile을 실행했다.
  - EC2 full-recovery 후 `codex_oauth` provider AI extraction artifact 10건과 canonical event impact가 생성됐다.
  - EC2 FastAPI/Next.js 서비스와 operating-data systemd timers 8개를 재시작했고, 주요 cockpit route를 로컬 SSH tunnel에서 확인했다.
- 막힌 점:
  - 없음.
- 아직 하지 않은 것:
  - `/recommendations` index route는 아직 없고, 현재 추천은 `/recommendations/<recommendationId>` 상세 또는 `/intelligence`에서 접근한다.
  - frontend route에서 개별 뉴스 candidate artifact 상세 표시는 기존 AI evidence 상세 화면을 통해 일부 가능하지만, 뉴스 전용 UX는 별도 개선 여지가 있다.

## Exact Next Step

- 다음 세션은 이것부터 시작: 추천 index route와 뉴스 전용 AI evidence UX를 추가해 사용자가 `/recommendations`, `/events`, `/intelligence`, `/stocks/<symbol>` 사이에서 근거 흐름을 끊기지 않고 볼 수 있게 한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_ai_extract tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_manual_local_ingest_smoke -v`: pass, 65 tests.
- `bash scripts/verify_news_ai_evidence_quality_pipeline.sh`: pass, 12 tests.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-ai-evidence-quality-pipeline`: pass.
- `git diff --check`: pass.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: failed on default Homebrew Python 3.14 due existing `pyexpat` dynamic library issue and missing FastAPI dependency.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: pass, 689 tests.
- `cd apps/web && npm run typecheck`: pass.
- `cd apps/web && npm run build`: pass.
  - Local DB dry-run: `news-rss-ai-extract-run --env-file /private/tmp/stockanalysis-runtime/data-operations.env --as-of-date 2026-05-21 --limit 3 --provider codex_oauth --dry-run`: pass, 3 planned candidates, no DB write/provider call.
- EC2 DB reset and migration/seed: pass, 51 tables after migration/seed.
- EC2 full recovery: pass, `run_status=completed`, 20/20 artifact steps succeeded.
- EC2 DB counts after full recovery: `ref.instrument=7575`, `ingest.source_document=23`, `event.event=20`, `event.event_classification_impact=21`, `event.event_instrument_impact=2`, `ai.model_invocation=10`, `ai.extraction_artifact=10`, `market.daily_price_bar=500`, `signal.recommendation=1`, `ops.pipeline_run=30`.
- EC2 latest pipeline status: `news_rss_upsert`, `news_rss_event_enrichment`, `event_intelligence_llm_extract`, `market_price_upsert` all succeeded on 2026-05-21 UTC.
- EC2 AI provider smoke: `ai.model_invocation` has `codex_oauth|succeeded|10`.
- EC2 services: `stockanalysis-frontend-api.service`, `stockanalysis-web.service` active; `stockanalysis-postgres` container up.
- EC2 timers: 8 `stockanalysis-operating-data-*` systemd timers active.
- Local tunnel UI smoke: `/`, `/data-health`, `/cycles`, `/events`, `/stocks`, `/intelligence`, `/paper-trading`, `/performance`, `/portfolio/coverage`, `/recommendations/AAPL-2024-11-01`, `/stocks/AAPL` returned 200 via `http://127.0.0.1:13000`.

## Risks

- `codex_oauth`는 Codex CLI 로그인/설치 상태에 의존한다.
- 새 runner는 AI 후보와 impact 반영을 만들지만, 추천 scoring 자체는 아직 변경하지 않는다.
- 외부 RAG/ontology 서비스는 도입하지 않았으므로 retrieval 품질은 기존 Postgres graph/context 품질에 제한된다.
