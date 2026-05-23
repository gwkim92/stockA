# Task Contract

## Task

- 이름: cycle-rag-graph-context
- 요청: Postgres ontology-lite를 기반으로 거시/도메인/테마 cycle graph context와 community summary를 만든다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 외부 RAG/그래프/vector 서비스 없이 Postgres에서 특정 cycle node의 parent/child graph, 최신 cycle state, 최근 이벤트, AI artifact, 전파 영향, 연결 종목/추천/보유 맥락을 한 번에 조회할 수 있고, 이 요약을 재사용 가능한 `ai.cycle_community_summary` row로 저장할 수 있다.

## Scope

- 포함:
  - `ai.cycle_community_summary` migration
  - node 중심 graph context SQL renderer
  - deterministic community summary runner
  - `cycle-graph-context-summary-run` CLI
  - `decision-daily` profile 연결
  - unit/bootstrap/AWH 검증
- 제외:
  - pgvector 도입
  - 외부 GraphRAG/Neo4j/RDF 서비스
  - 실시간 FastAPI 요청 중 LLM 호출
  - 추천 점수 산식 변경
  - 신규 프론트 화면

## Mutable Surface

- 수정 가능한 파일:
  - `db/migrations/`
  - `src/stockanalysis/ai/`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/`
  - `docs/tasks/cycle-rag-graph-context/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_graph_context tests.test_data_operations_cli tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_seed_bootstrap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task cycle-rag-graph-context`

## Done Criteria

- `ai.cycle_community_summary`가 migration으로 생성된다.
- `cycle-graph-context-summary-run --dry-run`은 DB write 없이 node context 요약 preview를 반환한다.
- `--execute`는 `ops.pipeline_run`과 summary rows를 저장한다.
- context SQL은 read-only이고 bounded limit을 가진다.
- `decision-daily`는 v2 cycle snapshot 이후 community summary를 갱신한다.
