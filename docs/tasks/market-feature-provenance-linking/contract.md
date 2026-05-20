# Task Contract

## Task

- 이름: market-feature-provenance-linking
- 요청: 추천 상세의 `market-feature-*` 점수 구성요소를 실제 feature snapshot, strategy universe rank, pipeline run 근거와 연결한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 상세 API는 가격 기반 점수 구성요소에 feature code/value/zscore/source run/evidence_json 요약을 제공한다.
  - `rank_score`는 가격 feature가 아니라 strategy universe rank/batch provenance로 표시된다.
  - 추천 상세 화면은 점수 입력의 출처를 사람이 이해 가능한 한국어로 보여준다.
  - 추천 점수 산식, DB schema, benchmark, LLM 호출, provider 호출, broker/order, scheduler behavior는 바꾸지 않는다.

## Scope

- 포함:
  - recommendation detail SQL read-only provenance CTE
  - recommendation score component DTO provenance
  - recommendation evidence review의 market/rank provenance gate
  - recommendation detail page provenance rendering
  - frontend example update
  - targeted tests and live smoke
- 제외:
  - scoring formula changes
  - recommendation generation changes
  - DB migration
  - real provider calls
  - live LLM/RAG calls
  - paper/live order write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/korean-labels.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/api/frontend/examples/recommendation-detail.json`
  - `docs/plans/2026-05-20-market-feature-provenance-linking.md`
  - `docs/tasks/market-feature-provenance-linking/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-feature-provenance-linking`
  - `git diff --check`

## Done Criteria

- [x] Recommendation detail SQL includes market feature and strategy universe provenance.
- [x] Recommendation detail API returns provenance for market/rank score components in tested fixture/live paths.
- [x] Recommendation page renders provenance in Korean without adding invalid links.
- [x] Frontend example documents the additive DTO fields.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
