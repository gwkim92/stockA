# Task Contract

## Task

- 이름: portfolio-attribution-bootstrap
- 요청: 장기 outcome과 position snapshot을 연결해 portfolio attribution을 저장한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `portfolio-attribution-bootstrap` CLI가 portfolio snapshot과 thesis outcome을 읽어 `performance.attribution_run`, `performance.attribution_component`에 security/theme/cash attribution row를 저장한다.

## Why

- 프로젝트는 중장기 투자 추천뿐 아니라 보유 판단이 잘 진행되고 있는지 지속 검토해야 한다. outcome만 있으면 추천 단위 성과는 알 수 있지만, 실제 포트폴리오의 기여 원인을 설명하기 어렵다.

## Scope

- 포함:
  - attribution run/component migration
  - deterministic attribution candidate lookup
  - `position_weighted_alpha_v1` attribution builder
  - CLI runner
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - 실거래 PnL
  - 주문/체결 연동
  - recommendation score 변경
  - thesis generation 변경
  - LLM 기반 판단
  - macro/cycle attribution 자동 분해

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0011_performance_attribution.sql`
  - `docs/db-schema-design.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/plans/2026-04-27-portfolio-attribution-bootstrap.md`
  - `docs/portfolio-attribution-bootstrap.md`
  - `docs/tasks/portfolio-attribution-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_portfolio_attribution_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/attribution.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_portfolio_attribution_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis generation rule
  - portfolio review action rule
  - benchmark/outcome schema unless attribution cannot reference it
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_portfolio_attribution_bootstrap.sh`
  - `bash scripts/verify_portfolio_attribution_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-attribution-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `performance.attribution_run` migration
  - `performance.attribution_component` migration
  - `portfolio-attribution-bootstrap` CLI
  - attribution unit tests
  - Docker verify script
  - task contract/plan/handoff/review

## Completion Criteria

- [x] attribution schema가 migration으로 추가된다.
- [x] attribution runner가 snapshot date와 measurement end date를 기준으로 outcome을 연결한다.
- [x] AAPL security selection contribution `30.0000` bps가 계산된다.
- [x] AAPL theme exposure contribution `30.0000` bps가 계산된다.
- [x] cash timing component가 cash weight `0.9500`, contribution `0.0000` bps로 저장된다.
- [x] Docker verify와 하네스 검증이 통과한다.
- [x] docs와 handoff가 갱신된다.

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/portfolio-attribution-bootstrap.md`에서 attribution 방법론과 LLM boundary가 명확한지 확인
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 attribution run 1건, component 3건, AAPL security/theme contribution `30.0000`, cash timing `0.0000`, latest `portfolio_attribution_bootstrap` run status `succeeded`다.

## Risks

- v1은 simplified attribution이다. full Brinson decomposition은 아니다.
- component가 double-count될 수 있으므로 consumer는 `component_type`별로 해석해야 한다.
- outcome이 없는 position은 v1에서 제외된다. 누락 coverage는 summary와 component count로 확인해야 한다.
