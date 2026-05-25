# Task Contract

## Task

- 이름: ai-equity-research-reporting
- 요청: 재무 정규화, 피어 비교, 밸류에이션, 뉴스/사이클, thesis를 종목별 한국어 AI 리서치 artifact로 묶는다.
- 담당: Codex
- 날짜: 2026-05-25

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations equity-research-reporting-run --as-of-date YYYY-MM-DD --provider fixture|codex_oauth --execute`가 `research.equity_research_artifact`에 `full_equity_research` artifact를 upsert하고, `ai.model_invocation`과 `ops.pipeline_run`에 호출/실행 기록을 남긴다.

## Scope

- 포함:
  - 종목별 Postgres research context 조회
  - Codex OAuth batch prompt/schema/provider boundary
  - fixture fallback provider
  - `research.equity_research_artifact` upsert
  - `ai.model_invocation` 기록
  - CLI, cadence, decision-daily profile 연결
  - unit/CLI/cadence/orchestrator tests
- 제외:
  - 추천 score/weight 변경
  - broker/live order submit
  - request-time AI 호출
  - 외부 유료 RAG/vector/graph DB
  - frontend redesign

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ai/equity_research_reporting.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/test_equity_research_reporting.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/ai-equity-research-reporting/*`
- 수정 금지 파일:
  - 추천 scoring formula/weights
  - benchmark/evaluation split
  - broker/order submit path
  - repo 안 secret/env 값

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_equity_research_reporting tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m stockanalysis.operations.cli equity-research-reporting-run --help`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task ai-equity-research-reporting`

## Done Criteria

- artifact는 한국어 summary, key points, catalysts, risks, invalidation, valuation sensitivity를 포함한다.
- AI 출력은 원천 context 밖의 종목/문서 id를 canonical 저장에 주입하지 않는다.
- AI 실패 시 fixture fallback으로 pipeline은 멈추지 않고 실패 invocation을 남긴다.
- 추천 score/weight는 변경하지 않는다.
