# Task Contract

## Task

- 이름: news-ai-eval-dataset-and-scoring
- 요청: 뉴스 AI 구조화 품질을 fixture/gold dataset으로 평가하고, direct ticker grounding, macro-only false ticker, quantum→energy 오분류, 번역 커버리지를 수치로 저장한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations news-ai-eval-run`이 gold dataset을 실행해 평가 점수를 만들고, `--execute` 시 `ai.eval_run`에 score JSON을 저장한다.

## Scope

- 포함:
  - macro-only, direct stock, quantum policy, energy shock, low-signal gold cases
  - 기존 `parse_news_ai_output`/`validate_news_ai_output` 재사용
  - theme precision, direct ticker grounding precision, macro-only false ticker rate, blocked correctness, Korean translation availability 계산
  - CLI와 unit/CLI tests
- 제외:
  - Codex OAuth real batch 평가
  - AI prompt/schema 변경
  - recommendation score weight 변경
  - data cleanup mutation
  - external vector/graph/RAG service

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/eval.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/fixtures/news_ai_eval_dataset_v1.json`
  - `tests/test_news_ai_eval.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/news-ai-eval-dataset-and-scoring/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations
  - recommendation scoring formula
  - live broker/order submit

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_ai_eval tests.test_data_operations_cli tests.test_news_rss_ai_extract`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-eval-dataset-and-scoring`

## Done Criteria

- gold dataset이 5개 이상 핵심 뉴스 유형을 포함한다.
- 평가 runner가 기존 validator를 실제로 사용한다.
- 목표 기준이 report에 명시된다.
- 기본 fixture 평가가 direct ticker false positive 0, macro-only false ticker 0, quantum→energy 0, Korean translation availability 100%를 통과한다.
- `--execute`가 `ai.eval_run` 저장 SQL을 실행한다.
