# market-cycle-intelligence-visual-hierarchy-v1 Handoff

## Current Status

- status: completed
- completed: `/intelligence`, `/cycle-map`, `/market-map` 상단 판단 카드와 주요 그리드의 데스크톱 시각 위계를 강화했다.
- changed: 세 페이지 루트와 hero section에 page-specific class를 추가했다.
- changed: `globals.css`에 1100px 이상 전용 asymmetric research desk layout을 추가했다.

## Implementation Notes

- `/intelligence`는 상단 판단 카드와 뉴스 근거 흐름 카드가 모두 같은 크기로 반복되지 않도록 첫 카드와 후속 evidence card의 span을 분리했다.
- `/cycle-map`은 첫 사이클 상태 카드와 첫 경로 행을 더 강하게 보여주도록 hierarchy를 추가했다.
- `/market-map`은 지표 품질, 가격 압력, 상위 체제, 추천 경계가 checkpoint board처럼 읽히도록 첫 rule/card에 emphasis를 줬다.
- 변경은 CSS/layout class 중심이며 API contract, schema, scheduler, scoring weight, benchmark, portfolio, broker/order boundary는 변경하지 않았다.

## Verification To Run

- exact next step: none; task completed and deployed, continue with the next roadmap task if requested.
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-visual-hierarchy-v1`
- passed: `git diff --check`
- passed: EC2 `git pull --ff-only origin develop`, `npm run typecheck`, `npm run build`, `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active.
- passed: EC2 internal route smoke for `/intelligence`, `/cycle-map`, `/market-map` returned 200, required layout classes rendered, forbidden operator wording absent.
- passed: local tunnel route smoke for `http://127.0.0.1:13000/intelligence`, `/cycle-map`, `/market-map` returned 200 with `research-command-deck`.
- visual evidence: `output/playwright/intelligence-visual-hierarchy.png`, `output/playwright/cycle-map-visual-hierarchy.png`, `output/playwright/market-map-visual-hierarchy.png` were generated for local review and are not intended for commit.

## Remaining Risk

- 모바일/tablet은 기존 breakpoint를 유지했고 새 규칙은 `min-width: 1100px`에만 적용했다.
- 더 큰 정보 구조 개편은 별도 task로 진행해야 한다. 이번 작업은 문구·데이터 의미 변경이 아니라 visual hierarchy 개선이다.
