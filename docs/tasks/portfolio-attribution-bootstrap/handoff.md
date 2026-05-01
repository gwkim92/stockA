# Session Handoff

## Active Task

- 이름: portfolio-attribution-bootstrap
- 담당: Codex
- 날짜: 2026-04-27

## Current Status

- 완료:
  - `performance.attribution_run`, `performance.attribution_component` migration을 추가했다.
  - `portfolio-attribution-bootstrap` runner와 CLI를 추가했다.
  - AAPL long horizon alpha `0.060000`과 weight `0.0500` 기반 security/theme contribution `30.0000` bps를 검증했다.
  - cash timing component는 weight `0.9500`, contribution `0.0000` bps로 저장된다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `db/migrations/0011_performance_attribution.sql`
  - `docs/plans/2026-04-27-portfolio-attribution-bootstrap.md`
  - `docs/portfolio-attribution-bootstrap.md`
  - `docs/tasks/portfolio-attribution-bootstrap/contract.md`
  - `docs/tasks/portfolio-attribution-bootstrap/plan.md`
  - `docs/tasks/portfolio-attribution-bootstrap/handoff.md`
  - `docs/tasks/portfolio-attribution-bootstrap/review.md`
  - `scripts/verify_portfolio_attribution_bootstrap.sh`
  - `src/stockanalysis/performance/attribution.py`
  - `tests/test_portfolio_attribution_bootstrap.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`

## Decisions

- attribution v1 methodology는 `position_weighted_alpha_v1`이다.
- LLM은 attribution 계산에 사용하지 않는다.
- cash timing은 미투자 weight를 표시하되 contribution은 0 bps로 둔다.
- security selection과 theme exposure는 같은 position contribution을 다른 관점으로 표현하므로 단순 합산하면 중복 해석될 수 있다.

## Verification Already Run

- `python3 -m compileall src tests`: 통과
- `PYTHONPATH=src python3 -m unittest tests.test_portfolio_attribution_bootstrap tests.test_ingest_cli -v`: 39 tests 통과
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: 196 tests 통과
- `bash -n scripts/verify_portfolio_attribution_bootstrap.sh`: 통과
- `bash scripts/verify_portfolio_attribution_bootstrap.sh`: 통과
  - 첫 실행은 sandbox Docker socket 권한으로 실패했고, 승인된 권한으로 재실행해 통과했다.
  - Docker Postgres에서 전체 196 tests와 attribution run/component assertion을 함께 확인했다.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-attribution-bootstrap`: 통과
- `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`: 출력 없음

## Still Unverified

- 실제 90/180/365일 장기 가격 history 기반 attribution
- outcome 없는 position의 coverage report
- macro/cycle attribution 자동 분해
- 실거래 체결 기준 PnL

## Exact Next Step

- 다음 세션은 이것부터 시작: scheduled outcome runner 또는 attribution coverage report를 구현한다.

## Risks

- v1은 simplified attribution이라 component 간 합산 의미를 엄격히 제한해야 한다.
- full Brinson decomposition은 아직 아니다.
