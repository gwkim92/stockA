# Task Contract

## Task

- 이름: local-ai-pipeline-run-alignment
- 요청: 무료 로컬 뉴스 클러스터 AI evidence 실행이 `/data-health`의 `event-intelligence-weekly` AI 분석 상태를 최신으로 갱신하게 한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations news-rss-cluster-evidence-run` 실행이 `ops.pipeline_run.pipeline_name='event_intelligence_llm_extract'`로 기록되어 `/api/data-health`의 `event-intelligence-weekly` 행이 최신 실행을 보여준다.

## Why

- 실제 `manual-local-ingest-smoke --execute`에서 `event-intelligence-weekly` artifact는 성공했다.
- 하지만 하위 runner가 DB에는 `news_rss_cluster_evidence`로 기록해서 data-health cadence row인 `event_intelligence_llm_extract`가 갱신되지 않았다.
- 운영자는 화면에서 AI 분석이 최신인지 봐야 하므로 artifact runner 성공과 canonical run history가 같은 작업으로 정렬되어야 한다.

## Scope

- 포함:
  - news RSS cluster evidence runner의 pipeline name override
  - operations CLI에서 data-health cadence pipeline name으로 기록
  - focused tests and verify script
  - local runtime command and data-health check
- 제외:
  - DB schema 변경
  - scoring/evaluation 변경
  - paid LLM/OpenAI call 도입
  - scheduler activation
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_news_rss_cluster_evidence.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_local_ai_pipeline_run_alignment.sh`
  - task docs, roadmap docs
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring
  - benchmark/evaluation split
  - host scheduler install files

## Boundaries

- 무료 로컬 규칙 기반 cluster evidence만 사용한다.
- live LLM/API call을 새로 만들지 않는다.
- 실제 `launchctl`이나 LaunchAgents write/delete는 하지 않는다.

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_local_ai_pipeline_run_alignment.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_news_rss_cluster_evidence tests.test_data_operations_cli`
  - authorized local `/api/data-health` check
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task local-ai-pipeline-run-alignment`
  - `git diff --check`

## Done Criteria

- [x] CLI passes `event_intelligence_llm_extract` to the local news cluster evidence runner.
- [x] Direct lower-level runner keeps legacy/default `news_rss_cluster_evidence` unless overridden.
- [x] Local runtime data-health shows AI row updated by the local evidence command.
- [x] Verification evidence is recorded.
