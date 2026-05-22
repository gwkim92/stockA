# Session Handoff

## Current Status

- 상태: local_verified
- 기준일: 2026-05-22
- 완료:
  - 작업 범위와 mutable surface를 `contract.md`에 고정했다.
  - root cause를 확인했다. cluster builder와 API superseding 기준이 모두 `theme_key`만 사용했다.
  - broad theme story fingerprint 구현과 프론트 story label 노출을 추가했다.
  - local unit/type/build 검증을 완료했다.
- 막힌 점:
  - 없음.

## Implemented

- `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `MARKET_NEWS_FLOW`, `UNCLASSIFIED`는 제목/요약 token fingerprint로 story cluster를 분리한다.
  - 구체 테마는 기존처럼 `story_key=theme`으로 유지한다.
  - `news_cluster_summary` output JSON에 `story_key`, `story_label`을 저장한다.
- `src/stockanalysis/frontend/live_adapter.py`
  - `/api/ai/news-clusters` 최신 artifact partition을 `theme_key + story_key` 기준으로 확장했다.
  - cluster DTO에 `story_key`, `story_label`을 추가했다.
- `apps/web`
  - `/intelligence` 카드 제목을 story label로 보여주고 상위 테마를 별도 표기한다.
  - `/ai-evidence/...` 뉴스 묶음 상세에서도 story label과 상위 테마를 구분한다.

## Verification

- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_cluster_evidence tests.test_frontend_live_adapter`
- PASS: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `git diff --check`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-cluster-story-fingerprint`

## Remaining

- Commit and push.
- Deploy to EC2, restart services, regenerate news cluster artifacts, and smoke `/api/ai/news-clusters?limit=10` plus `/intelligence`.

## Exact Next Step

- exact next step: commit and push `news-cluster-story-fingerprint`, then deploy it to EC2.

## Remaining Risks

- Title-token fingerprint is deterministic and free, but it is not semantic clustering. Similar articles with different wording may still split until AI/RAG clustering improves.
