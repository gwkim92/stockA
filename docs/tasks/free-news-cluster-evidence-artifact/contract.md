# Task Contract

## Task

- 이름: free-news-cluster-evidence-artifact
- 요청: 무료 RSS 뉴스 묶음 분석을 DB에 감사 가능한 AI evidence artifact로 저장한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 최신 RSS 뉴스 묶음을 테마 기준으로 요약한 `news_cluster_summary` artifact가 `ai.extraction_artifact`에 저장될 수 있다.
  - 저장은 `local_rules` provider, 0 token, 0 cost로 기록되어 유료 API/LLM 호출이 없음을 감사할 수 있다.
  - 대표 이벤트에 artifact가 연결되어 기존 `/api/events`와 `/api/ai-evidence/...` 경계에서 추적 가능하다.
  - 기존 DB schema, recommendation scoring, broker/order flow는 변경하지 않는다.

## Scope

- 최근 enriched RSS 이벤트를 읽어 테마별 cluster summary를 만든다.
- operations CLI에 단발 실행 command를 추가한다.
- 중복 방지를 위해 같은 입력 이벤트 집합의 request hash가 이미 있으면 skip한다.
- 단위 테스트와 handoff를 남긴다.

## Boundaries

- LLM, paid news provider, external translation API를 호출하지 않는다.
- artifact는 추천/보유 판단을 자동 변경하지 않는다.
- DB schema와 frontend DTO contract는 변경하지 않는다.
- 실거래, broker submission, scheduler host mutation은 범위 밖이다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/models.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_news_rss_cluster_evidence.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/free-news-cluster-evidence-artifact/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_cluster_evidence tests.test_data_operations_cli`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src/stockanalysis/ingest/news src/stockanalysis/operations/cli.py tests/test_news_rss_cluster_evidence.py`
  - real DB dry-run: `stockanalysis-operations news-rss-cluster-evidence-run --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --dry-run`
  - real DB run: `stockanalysis-operations news-rss-cluster-evidence-run --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - authenticated FastAPI `/api/events` smoke shows new `ai_evidence_id` on representative news events.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-news-cluster-evidence-artifact`
  - `git diff --check`

## Done Criteria

- [x] cluster evidence command exists and is callable through backend operations CLI.
- [x] dry-run reports planned clusters without DB writes.
- [x] real local DB can insert at least one `news_cluster_summary` artifact.
- [x] new artifact is visible through existing read-only API/evidence boundary.
- [x] required verification passes.
