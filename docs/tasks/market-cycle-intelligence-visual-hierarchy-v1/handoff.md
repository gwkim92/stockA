# market-cycle-intelligence-visual-hierarchy-v1 Handoff

## Current Status

- status: implemented_locally_pending_verification
- in progress: `/intelligence`, `/cycle-map`, `/market-map` 상단 판단 카드와 주요 그리드의 데스크톱 시각 위계를 강화했다.
- changed: 세 페이지 루트와 hero section에 page-specific class를 추가했다.
- changed: `globals.css`에 1100px 이상 전용 asymmetric research desk layout을 추가했다.

## Implementation Notes

- `/intelligence`는 상단 판단 카드와 뉴스 근거 흐름 카드가 모두 같은 크기로 반복되지 않도록 첫 카드와 후속 evidence card의 span을 분리했다.
- `/cycle-map`은 첫 사이클 상태 카드와 첫 경로 행을 더 강하게 보여주도록 hierarchy를 추가했다.
- `/market-map`은 지표 품질, 가격 압력, 상위 체제, 추천 경계가 checkpoint board처럼 읽히도록 첫 rule/card에 emphasis를 줬다.
- 변경은 CSS/layout class 중심이며 API contract, schema, scheduler, scoring weight, benchmark, portfolio, broker/order boundary는 변경하지 않았다.

## Verification To Run

- exact next step: `cd apps/web && npm run typecheck`
- next: `cd apps/web && npm run build`
- next: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task market-cycle-intelligence-visual-hierarchy-v1`
- next: `git diff --check`

## Remaining Risk

- 데스크톱 시각 위계는 CSS로 적용됐지만 실제 EC2 route smoke와 브라우저 시각 확인 전까지 최종 완료로 보지 않는다.
- 모바일/tablet은 기존 breakpoint를 유지했고 새 규칙은 `min-width: 1100px`에만 적용했다.
