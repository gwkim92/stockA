# Session Handoff

## Active Task

- 이름: frontend-flow-wording-and-market-holidays
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract and plan created.
  - repo 밖 실행 env `/private/tmp/stockanalysis-runtime/data-operations.real.env`에 2026년 미국장 full-closure 휴장일 10개를 추가했다.
  - freshness policy env를 `latest_completed_us_market_day`, data-ready local time을 `18:30`으로 명시했다.
  - 홈 화면에 end-to-end 시스템 플로우를 추가했다: 수집 → 적재/정규화 → 상태 점검 → 신호 생성 → 사람 검토 → 성과 추적.
  - 상단 네비게이션과 주요 페이지 워딩을 한국어 운영 화면 기준으로 정리했다.
  - `korean-labels.ts`를 보강해 pipeline, domain, freshness, scheduler, event, thesis, recommendation raw code 노출을 줄였다.
  - Chrome에서 `/`, `/data-health`, `/cycles`, `/events`, `/recommendations/...`, `/theses/...`, `/portfolio/coverage`를 직접 확인했다.
- 진행 중:
  - none.
- 막힌 점:
  - none yet.

## Exact Next Step

- exact next step: if continuing UI quality work, convert remaining detail pages from inline styles to shared page sections and add richer empty/error states. If continuing backend/product work, return to local live MVP data source quality and real portfolio source integration.

## Verification

- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - 2026-05-25 holiday skip policy check resolved freshness target `2026-05-22` with 10 configured non-trading dates.
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Route smoke returned 200 for `/`, `/data-health`, `/cycles`, `/events`, `/themes/ANNUAL_REPORTING`, `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`, `/performance`, `/ai-evidence/ai-evidence-1`, `/source-documents/source-document-0000320193-24-000123`, `/remediation`.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-flow-wording-and-market-holidays`
  - `git diff --check`

## Risks

- 화면은 운영 흐름을 더 잘 설명하지만, 아직 일부 detail page는 inline style 중심이다.
- 실제 투자 추천 품질, AI RAG/ontology, 페이퍼/실거래는 이 task 범위 밖이다.
- 휴장일은 외부 calendar API가 아니라 repo 밖 env 수동 유지 방식이다. 2027년 이후와 조기 폐장 정책은 별도 운영 관리가 필요하다.
