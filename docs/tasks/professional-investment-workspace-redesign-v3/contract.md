# professional-investment-workspace-redesign-v3 Contract

## Task Request

- request: 운영자 cockpit 중심의 전체 프론트엔드를 한국인 개인 투자자가 매일 사용하는 전문 투자 리서치 워크스페이스로 재구성한다.
- context: 기존 URL과 API DTO는 유지하고, 투자 화면과 운영 콘솔을 분리하며, 추천 점수·DB schema·AI 분석·포트폴리오 포지션·주문 경계는 변경하지 않는다.

## Goal

- goal: `오늘 → 시장 → 사이클·뉴스 → 종목 → 추천 → 포트폴리오·성과` 판단 흐름이 1차 메뉴와 핵심 페이지에 일관되게 적용되고, 운영 정보는 별도 관리 화면에서만 상세 노출된다.

## Mutable Surface

- mutable surface:
  - `DESIGN.md`
  - `docs/frontend-product-map.md`
  - `docs/tasks/professional-investment-workspace-redesign-v3/*`
  - `apps/web/`

## Invariants

- DB schema, ingest, AI extraction, validator, cycle calculation, recommendation score/weight, benchmark, portfolio position을 변경하지 않는다.
- broker submit과 실거래 자동화를 열지 않는다.
- 기존 public route와 frontend API DTO를 유지한다.
- 유료 디자인·차트 서비스를 추가하지 않는다.

## Scope

- 제품 지도와 디자인 토큰을 고정한다.
- 한국어 투자자용 presentation 계층과 공통 상태·요약·목록 컴포넌트를 만든다.
- 전역 셸과 1차 내비게이션을 투자 판단 순서로 바꾼다.
- 홈, 시장, 사이클, 뉴스, 종목, 추천, 포트폴리오, 성과, 가상 매매의 첫 결론과 정보 위계를 정리한다.
- 데이터 상태, AI 운영, 거래 안전, 보완 작업을 공통 운영 콘솔로 분리한다.
- 모바일, 접근성, 내부 용어 노출을 자동 검증한다.

## Verification Commands

- verification command: `cd apps/web && npm test`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `cd apps/web && STOCKANALYSIS_WEB_BASE_URL=http://127.0.0.1:13003 npm run test:e2e`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest discover -s tests`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task professional-investment-workspace-redesign-v3`
- verification command: `git diff --check`

## Acceptance Criteria

- 1차 메뉴는 `오늘`, `시장`, `리서치`, `종목`, `추천`, `포트폴리오`다.
- 투자 화면은 내부 실행 용어보다 결론, 수치, 근거, 위험을 먼저 보여준다.
- 운영 화면은 데이터, AI, 거래 안전, 보완 작업으로 분리된다.
- 390px와 desktop에서 가로 넘침이 없다.
- 핵심 화면에 serious/critical axe 위반이 없다.
- 추천 산식, benchmark, portfolio position, broker/order boundary가 변경되지 않는다.
