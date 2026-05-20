# Local AI Pipeline Run Alignment

생성일: 2026-05-20

## 목적

무료 로컬 뉴스 클러스터 evidence 실행이 `/data-health`의 `event-intelligence-weekly` 상태를 최신으로 갱신하게 한다.

## 문제

수동 ingest smoke에서 `event-intelligence-weekly` artifact는 성공했지만, 하위 runner는 `ops.pipeline_run.pipeline_name='news_rss_cluster_evidence'`로 기록했다.

반면 `/api/data-health`의 cadence registry는 `event-intelligence-weekly`를 `event_intelligence_llm_extract`로 본다. 그래서 실제 실행은 성공했는데 화면의 AI 분석 row는 이전 날짜로 남았다.

## 해결

- 하위 `run_news_rss_cluster_evidence`는 기본 pipeline name을 `news_rss_cluster_evidence`로 유지한다.
- `stockanalysis-operations news-rss-cluster-evidence-run`은 data-health cadence와 맞추기 위해 `event_intelligence_llm_extract`로 run history를 기록한다.
- 이 실행은 무료 로컬 규칙 기반 evidence이며, 새 유료 LLM 호출을 만들지 않는다.

## 경계

- DB schema는 바꾸지 않는다.
- scoring/evaluation은 바꾸지 않는다.
- scheduler activation은 하지 않는다.
- broker/order flow는 건드리지 않는다.
