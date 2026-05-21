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
- 막힌 점:
  - 없음.
- 아직 하지 않은 것:
  - EC2에서 실제 `codex_oauth` dry-run/execute smoke.
  - EC2 scheduler manifest 재생성 및 service/timer reload.
  - frontend route에서 개별 뉴스 candidate artifact 상세 표시.

## Exact Next Step

- 다음 세션은 이것부터 시작: focused local verification과 AWH 검증을 완료한 뒤, EC2에 배포해 `news-rss-ai-extract-run --provider codex_oauth --limit 10 --execute`를 1회 수동 smoke하고 `/api/data-health`와 화면에서 `event-intelligence-weekly` 최신 상태를 확인한다.

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

## Risks

- `codex_oauth`는 Codex CLI 로그인/설치 상태에 의존한다.
- 새 runner는 AI 후보와 impact 반영을 만들지만, 추천 scoring 자체는 아직 변경하지 않는다.
- 외부 RAG/ontology 서비스는 도입하지 않았으므로 retrieval 품질은 기존 Postgres graph/context 품질에 제한된다.
