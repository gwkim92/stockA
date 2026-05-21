# Task Contract

## Task

- 이름: news-dedup-symbol-classification-root-cause
- 요청: 같은 뉴스가 여러 묶음과 후보 목록에 반복 노출되는 원인을 확인하고 근본 해결한다. `종목 미분류`가 왜 발생하는지 실제 데이터와 분류 경계 기준으로 설명 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-21

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 같은 `news_rss_item` event가 단순 SQL 조인 증폭 때문에 event list, AI 후보, news cluster에 반복 노출되지 않고, 명확한 회사명 뉴스는 `ref.instrument` alias 기반으로 canonical instrument impact 후보가 된다.

## Scope

- 포함:
  - EC2 live DB에서 중복 뉴스와 미분류 종목 사례 확인
  - frontend live API event list/query의 event x theme x instrument row 증폭 제거
  - news cluster evidence 후보/cluster 생성의 event 단위 중복 제거
  - `ref.instrument.name` 기반 company alias lookup 추가
  - 기존 artifact를 새 로직으로 재생성하거나 최신 artifact가 새 로직을 반영하도록 EC2 smoke 수행
  - `종목 미분류`는 진짜 단일 종목이 없는 macro/theme 뉴스와 분류 누락을 구분해 보고
- 제외:
  - 신규 유료 데이터 공급자 도입
  - DB schema 대규모 변경
  - 추천 점수 모델, broker/order flow, 실거래 자동화 변경
  - 외부 vector DB/graph DB 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/ingest/news/enrichment.py`
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_news_rss_enrichment.py`
  - `tests/test_news_rss_cluster_evidence.py`
  - `docs/tasks/news-dedup-symbol-classification-root-cause/`
- 수정 금지 파일:
  - `.env` secret values
  - DB schema/migrations
  - scoring formula
  - broker/order submission code

## Acceptance Criteria

- 같은 `event_id`/source news가 frontend event list와 AI 후보 목록에서 단순 조인 증폭으로 중복 노출되지 않는다.
- cluster evidence 생성 쿼리는 한 이벤트를 기본적으로 하나의 primary theme cluster에만 배치한다.
- 테스트가 중복 방지 SQL 의도를 검증한다.
- EC2에서 새 코드 배포 후 cluster/evidence API가 새 로직으로 동작하는지 확인한다.
- `종목 미분류` 발생 원인과 남은 한계를 handoff에 기록한다.

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src python3 -m unittest tests.test_news_rss_cluster_evidence tests.test_news_rss_enrichment tests.test_frontend_live_adapter tests.test_news_rss_ai_extract`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/test-venv/bin/python -m unittest discover -s tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task news-dedup-symbol-classification-root-cause`
  - EC2 DB read-only SQL smoke for company alias lookup and cluster candidate dedupe
  - EC2 deploy 후 `news-intraday` 또는 관련 enrichment/cluster 단계 수동 1회 실행

## Done Criteria

- [x] Frontend event list SQL이 primary impact만 선택한다.
- [x] Cluster evidence 후보 SQL과 builder가 event를 한 cluster에만 배치한다.
- [x] Company alias lookup이 `Analog Devices`, `Intuit`, `Target` 같은 명확한 회사명 뉴스를 symbol로 연결한다.
- [x] EC2 최신 artifact/API에서 event `11`, `19`가 중복 cluster로 보이지 않는다.
