# Session Handoff

## Active Task

- 이름: local-ai-pipeline-run-alignment
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract and implementation plan created.
  - `run_news_rss_cluster_evidence` now accepts an explicit `pipeline_name`.
  - lower-level/direct runner default remains `news_rss_cluster_evidence`.
  - `stockanalysis-operations news-rss-cluster-evidence-run` records run history as `event_intelligence_llm_extract`.
  - focused unit tests cover default behavior, override behavior, invalid empty pipeline name, and CLI override wiring.
  - focused verification script added.
  - local runtime command ran successfully against `/private/tmp/stockanalysis-runtime/data-operations.env`.
  - authorized `/api/data-health` showed `event-intelligence-weekly` updated through `pipeline-run-143` on 2026-05-20.
  - EC2 runtime command also ran successfully after RSS enrichment:
    - `news-rss-enrich-run`: 20 events enriched, 2 instrument impacts linked.
    - `news-rss-cluster-evidence-run`: 20 candidate events, 3 clusters, 3 local-rule AI evidence artifacts inserted.
    - authorized `/api/ai/news-clusters?asOfDate=2026-05-20&limit=4`: 3 clusters returned.
- 막힌 점:
  - none for this task.
  - 별도 운영 readiness blocker: EC2 data operations strict env readiness fails because `STOCKANALYSIS_CODEX_CLI_COMMAND=codex` is not installed/authenticated on EC2. The local-rule cluster evidence path itself does not call a paid LLM and succeeded.

## Exact Next Step

- 다음 세션은 이것부터 시작: 수동 실행으로 검증된 market/news/AI jobs를 안전한 local 반복 실행 worker로 묶을지, 아니면 data-health 운영자 화면의 남은 수집/분석 상태 설명을 먼저 고도화할지 task contract로 고정한다.
- 금지: 명시 승인 전까지 `launchctl bootstrap/kickstart`, `~/Library/LaunchAgents` write/delete, external scheduler deployment는 하지 않는다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_cluster_evidence tests.test_data_operations_cli`
- `bash scripts/verify_local_ai_pipeline_run_alignment.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-ai-pipeline-run-alignment`
- `git diff --check`
- Runtime command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli news-rss-cluster-evidence-run --env-file /private/tmp/stockanalysis-runtime/data-operations.env`
- Runtime API check: authorized `GET http://127.0.0.1:8787/api/data-health` returned `pipeline_name=event_intelligence_llm_extract`, `job_id=event-intelligence-weekly`, `latest_run_id=pipeline-run-143`, `latest_status=succeeded`, and `health_status=ok`.
- Runtime page check: `GET http://127.0.0.1:3001/data-health` rendered the AI analysis row with the 2026-05-20 completion timestamp.
- EC2 runtime evidence:
  - `ai.extraction_artifact`: `3`
  - `ai.model_invocation`: `3`
  - `event.event_classification_impact`: `20`
  - authorized `GET http://127.0.0.1:8787/api/ai/news-clusters?asOfDate=2026-05-20&limit=4` returned `cluster_count=3`.

## Risks

- This alignment fixes run-history visibility only. It does not add a paid LLM provider, new recommendation scoring, paper/live trading automation, or scheduler activation.
- Existing local FastAPI/Next processes may need restart after code changes in sessions that do not use auto-reload.
- EC2 has not installed/authenticated Codex CLI yet, so `codex_oauth` is not a working recurring LLM execution boundary on the server.
