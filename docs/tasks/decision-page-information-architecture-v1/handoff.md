# decision-page-information-architecture-v1 Handoff

## Current Status

- status: completed
- completed: 주요 판단 화면의 반복 섹션을 줄이고 투자자가 읽는 순서를 정리했다.
- changed: `/intelligence`의 개별 근거, 차단 항목, 추천 연결 섹션을 `판단 대기열` 하나로 통합했다.
- changed: `/cycle-map`의 중복 attention strip을 제거하고 `오늘 가장 먼저 읽을 사이클` 보드로 우선순위를 단일화했다.
- changed: `/market-map`의 반복 `오늘 결론` 패널과 `시장 체크포인트` 행을 제거하고 상관관계와 압력판을 바로 노출했다.
- changed: `decision-triage-*` CSS를 추가해 근거 후보를 넓게, 차단/추천 경계를 짧게 비교하도록 배치했다.

## Implementation Notes

- 데이터 fetch, API response, database schema, scheduler, scoring weight, benchmark, portfolio, paper records, broker/order boundary는 변경하지 않았다.
- `/market-map`의 상관관계 분석은 삭제하지 않고 hero 바로 아래로 올렸다.
- `/intelligence`의 기존 전용 경로 링크는 유지했다: 근거 후보, 차단 목록, 추천 영향, 가상 매매 상태.
- 모바일/tablet에서는 판단 대기열이 1열로 접힌다.

## Verification To Run

- exact next step: none; task completed and deployed, continue with the next roadmap task if requested.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-page-information-architecture-v1`
- passed: `git diff --check`
- passed: EC2 `git pull --ff-only origin develop`, `npm run typecheck`, `npm run build`, `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active.
- passed: EC2 internal route smoke for `/intelligence`, `/cycle-map`, `/market-map`.
- passed: local tunnel smoke for `http://127.0.0.1:13000/intelligence`, `/cycle-map`, `/market-map`.
- visual evidence: `output/playwright/intelligence-ia-v1.png`, `output/playwright/cycle-map-ia-v1.png`, `output/playwright/market-map-ia-v1.png` generated for local review and not intended for commit.

## Remaining Risk

- 이번 작업은 화면 정보 구조 정리이며, 더 깊은 전체 네비게이션/페이지 통폐합은 별도 task로 다룬다.
