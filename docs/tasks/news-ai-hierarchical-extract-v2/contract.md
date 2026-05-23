# Task Contract

## Task

- 이름: news-ai-hierarchical-extract-v2
- 요청: 뉴스 AI output을 거시/도메인/테마/직접 종목/인과 경로/근거 span으로 분리한다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: Codex OAuth 뉴스 분석은 개별 종목 뉴스와 상위 흐름 뉴스를 분리해서 저장 가능한 구조로 반환하고, validator는 검증된 상위 node impact와 직접 종목 impact만 canonical table에 반영한다.

## Scope

- 포함:
  - hierarchical news AI output schema v3
  - 기존 v2 fixture 호환 parser
  - macro/domain/theme impact validator 연결
  - direct instrument impact 분리
  - causal path, evidence span artifact 저장
  - frontend live adapter의 v2/v3 artifact 호환
- 제외:
  - multi-hop propagation v2 테이블
  - cycle hierarchy snapshot v2
  - recommendation formula 변경
  - 실거래 또는 broker submit

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_news_rss_ai_extract.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/news-ai-hierarchical-extract-v2/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - DB schema migration
  - broker/live order submission

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract tests.test_frontend_live_adapter`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task news-ai-hierarchical-extract-v2`

## Done Criteria

- prompt/schema가 `macro_regime_impacts`, `domain_impacts`, `theme_impacts`, `direct_instrument_impacts`, `causal_paths`, `evidence_spans`를 요구한다.
- 기존 `theme_impacts`/`instrument_impacts` artifact도 깨지지 않는다.
- macro-only 뉴스는 직접 종목 impact 없이 classification impact로 검증된다.
- 프론트 live adapter는 v2/v3 artifact를 모두 읽는다.
