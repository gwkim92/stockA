# Session Handoff

## Current Status

- 상태: ec2_verified
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - root cause를 확인했다. cluster builder와 API superseding 기준이 모두 `theme_key`만 사용했다.
  - broad theme story fingerprint 구현과 프론트 story label 노출을 추가했다.
  - local unit/type/build 검증을 완료했다.
  - EC2에 배포했고 `news_rss_cluster_evidence` artifact를 재생성했다.
- 막힌 점:
  - 없음.

## Implemented

- `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `MARKET_NEWS_FLOW`, `UNCLASSIFIED`는 제목/요약 token fingerprint로 story cluster를 분리한다.
  - broad theme의 단발·무종목 뉴스는 cluster evidence로 승격하지 않는다.
  - 구체 테마는 기존처럼 `story_key=theme`으로 유지한다.
  - `news_cluster_summary` output JSON에 `story_key`, `story_label`을 저장한다.
- `src/stockanalysis/frontend/live_adapter.py`
  - `/api/ai/news-clusters` 최신 artifact partition을 `theme_key + story_key` 기준으로 확장했다.
  - 새 story-split artifact가 존재하는 broad theme에서는 과거 `story_key` 없는 단일 theme artifact를 숨긴다.
  - 목록 정렬은 artifact 생성시간보다 묶인 뉴스 수를 우선한다. `/intelligence`가 단발 뉴스보다 큰 흐름을 먼저 보게 하기 위한 기준이다.
  - cluster DTO에 `story_key`, `story_label`을 추가했다.
- `apps/web`
  - `/intelligence` 카드 제목을 story label로 보여주고 상위 테마를 별도 표기한다.
  - `/intelligence`의 개별 뉴스 후보 큐는 `news_event_candidate`만 보여주고 `news_cluster_summary` 대표 이벤트는 제외한다.
  - `/ai-evidence/...` 뉴스 묶음 상세에서도 story label과 상위 테마를 구분한다.

## Verification

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_cluster_evidence tests.test_frontend_live_adapter`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-cluster-story-fingerprint`
- PASS: after stale broad-theme guard, `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_news_rss_cluster_evidence`
- PASS: after stale broad-theme guard, `git diff --check`
- PASS: after broad single-no-symbol noise filter, `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_cluster_evidence tests.test_frontend_live_adapter`
- PASS: after broad single-no-symbol noise filter, `git diff --check`
- PASS: after cluster ordering fix, `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_news_rss_cluster_evidence`
- PASS: after cluster ordering fix, `git diff --check`
- PASS: after candidate queue filter, `cd apps/web && npm run typecheck`
- PASS: after candidate queue filter, `cd apps/web && npm run build`
- PASS: after candidate queue filter, `git diff --check`
- PASS: EC2 HEAD `2ff9389`, services `stockanalysis-web.service` and `stockanalysis-frontend-api.service` active.
- PASS: EC2 `news-rss-cluster-evidence-run --as-of-date 2026-05-22 --event-limit 120 --max-clusters 12` inserted 12 artifacts, failed 0.
- PASS: EC2 `/api/ai/news-clusters?limit=4` returns top clusters by event count: `MACRO_RATES_FED` 19, `ENERGY_GEOPOLITICS` 11, `US_MARKET_BREADTH` 9, `AI_SEMICONDUCTOR_CYCLE` 7.
- PASS: EC2 `/api/ai/news-clusters?limit=4` has `broad_theme_without_story=[]`.
- PASS: local tunnel `/intelligence` HTTP 200, no server component error, macro and energy clusters visible, personal-finance broad-theme noise absent from candidate queue.
- PASS: Playwright snapshot for `http://127.0.0.1:13000/intelligence` shows major clusters first and candidate queue no longer lists `news_cluster_summary` entries.

## Remaining

- Event list still marks many representative events with `ai_evidence_type=news_cluster_summary`. `/intelligence` now filters them out of the candidate queue, but `/events` should be reviewed next so cluster summaries are not presented as individual AI candidate analysis.

## Exact Next Step

- exact next step: audit `/events` and AI evidence list wording so `news_cluster_summary` and `news_event_candidate` are clearly separated everywhere.

## Remaining Risks

- Title-token fingerprint is deterministic and free, but it is not semantic clustering. Similar articles with different wording may still split until AI/RAG clustering improves.
