# Task Contract

## Task

- 이름: news-cluster-automation-regression
- 요청: EC2 실제 데이터에서 `news_cluster_summary`가 생성되지 않는 회귀를 원인 확인 후 복구한다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `news-intraday` 자동 실행 프로필이 RSS 수집, RSS 이벤트 enrichment, 뉴스 묶음 evidence 생성, Codex OAuth 뉴스 AI 후보 생성을 모두 순서대로 실행한다.

## Root Cause

- DB reset 이후 재적재 경로에서 `event-intelligence-weekly`가 `news-rss-ai-extract-run`만 실행했다.
- 과거 `news-rss-cluster-evidence-run`으로 생성됐던 `news_cluster_summary` artifact는 reset으로 사라졌고, 최신 자동 프로필에서 다시 생성되지 않았다.
- 그 결과 EC2 DB에는 `news_event_candidate` artifact만 남고 `news_cluster_summary`가 0건이었다.

## Scope

- 포함:
  - `news-intraday` operating-data profile에 `news-cluster-evidence` 단계를 복구
  - cluster evidence 생성 후 AI candidate 분석이 실행되도록 순서 고정
  - 자동화 계획/테스트/문서 갱신
  - EC2에서 수동 1회 실행해 실제 cluster artifact 생성 확인
- 제외:
  - 추천 산식 변경
  - DB migration
  - paid provider 도입
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/local_runtime_status.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/news-cluster-automation-regression/`
- 수정 금지 파일:
  - `.env` secret values
  - DB schema/migrations
  - scoring formula
  - broker/order submission code

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract -v`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-cluster-automation-regression`
  - EC2 deploy 후 `news-intraday` profile 수동 1회 실행
  - EC2 DB에서 `ai.extraction_artifact.artifact_type='news_cluster_summary'` count > 0 확인
  - authorized `/api/ai/news-clusters?asOfDate=<date>&limit=4`가 cluster를 반환하는지 확인

## Done Criteria

- [ ] `news-intraday` planned steps에 `news-cluster-evidence`와 `news-ai-evidence`가 모두 존재한다.
- [ ] cluster evidence가 AI candidate보다 먼저 실행된다.
- [ ] EC2 DB에 `news_cluster_summary` artifact가 실제 생성된다.
- [ ] `/intelligence`에서 뉴스 묶음 section이 다시 데이터를 표시한다.
