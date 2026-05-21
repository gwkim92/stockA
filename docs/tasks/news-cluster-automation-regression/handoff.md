# Session Handoff

## Active Task

- 이름: news-cluster-automation-regression
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 진행 중:
  - EC2 실제 DB에서 `news_event_candidate=10`, `news_cluster_summary=0` 상태를 확인했다.
  - 이전 00:38 실행 리포트에는 cluster 3건 생성 기록이 있었지만, 이후 DB reset/recovery로 사라진 것을 확인했다.
  - 최신 자동 프로필이 AI 후보 분석만 실행하고 cluster evidence를 재생성하지 않는 회귀를 원인으로 판단했다.
  - `news-intraday` operating-data profile에 `news-cluster-evidence` 단계를 AI 후보 분석 앞에 복구했다.
  - cadence/local runtime manual command도 단일 AI extract가 아니라 `operating-data-run --profile news-intraday`를 안내하도록 정렬했다.

## Exact Next Step

- exact next step: EC2에 배포한 뒤 `news-intraday` profile을 1회 실행하고 `news_cluster_summary` artifact와 `/api/ai/news-clusters` 응답을 확인한다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cadence tests.test_news_rss_cluster_evidence tests.test_news_rss_ai_extract -v`: pass, 28 tests.

## Risks

- 이번 수정은 자동화 단계 복구이며 추천 산식이나 주문/거래 실행은 바꾸지 않는다.
