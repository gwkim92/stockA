# Task Contract

## Task

- 이름: news-cluster-story-fingerprint
- 요청: `/intelligence` 화면의 뉴스 묶음이 서로 무관한 뉴스를 같은 테마 아래 한 카드로 보여주는 문제를 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `MARKET_NEWS_FLOW`처럼 넓은 테마의 서로 다른 뉴스가 한 클러스터로 뭉치지 않는다.
  - 같은 넓은 테마 안의 여러 story cluster가 `/api/ai/news-clusters`에서 동시에 보일 수 있다.
  - `/intelligence`와 `/ai-evidence/...`는 `상위 테마`와 `스토리/이슈`를 구분해서 보여준다.
  - 기존 구체 테마 클러스터 동작은 유지한다.

## Scope

- 포함:
  - 넓은 뉴스 테마의 제목/요약 기반 deterministic story fingerprint
  - `news_cluster_summary` artifact의 `story_key`, `story_label` 저장
  - `/api/ai/news-clusters` 최신 artifact 선택 기준을 `theme_key + story_key`로 확장
  - 프론트 타입과 `/intelligence`, `/ai-evidence/...` 문구 보강
  - focused unit tests와 local/EC2 smoke
- 제외:
  - 유료 뉴스 API 도입
  - 외부 vector DB, Neo4j, RDF store 도입
  - 추천 산식 변경
  - 실거래 또는 주문 자동화

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/ingest/news/models.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/globals.css`
  - `tests/test_news_rss_cluster_evidence.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/news-cluster-story-fingerprint/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler systemd units or host launch agents
  - recommendation scoring weights

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_cluster_evidence tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-cluster-story-fingerprint`
  - EC2 authorized smoke for `/api/ai/news-clusters?limit=10`
  - EC2 `/intelligence` render smoke

## Done Criteria

- [ ] Broad market-flow news is split by deterministic story fingerprint.
- [ ] API latest-artifact partition keeps multiple story clusters under the same theme.
- [ ] Frontend shows story label and parent theme separately.
- [ ] EC2 has regenerated cluster artifacts with `story_key` and `/intelligence` renders without server component error.
