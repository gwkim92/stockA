# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: market-price-universe-backfill
- 담당: Codex
- 날짜: 2026-04-23

## Current Status

- 완료:
  - task 범위와 검증 계획을 문서로 고정했다.
  - canonical symbol selection, backfill runner, CLI, fixture, verify, 운영 문서를 구현했다.
- 막힌 점:
  - 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-23-market-price-universe-backfill.md`
  - `docs/market-price-universe-backfill.md`
  - `docs/tasks/market-price-universe-backfill/contract.md`
  - `docs/tasks/market-price-universe-backfill/plan.md`
  - `docs/tasks/market-price-universe-backfill/handoff.md`
  - `docs/tasks/market-price-universe-backfill/review.md`
  - `scripts/verify_market_price_universe_backfill.sh`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `tests/test_market_backfill.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_BABA.json`
- 수정:
  - `README.md`
  - `docs/verification-plan.md`
  - `docs/tasks/market-universe-bootstrap/handoff.md`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - migrations and seeds
  - SEC companyfacts/event logic

## Decisions

- 결정:
  - canonical active symbol lookup 결과를 existing `run_market_price_batch_upsert`에 그대로 넘긴다.
  - `Nasdaq`, `NYSE` filter semantics는 universe bootstrap과 맞춘다.
  - current task는 orchestration layer만 추가하고 price upsert logic 자체는 건드리지 않는다.
- 이유:
  - 이미 검증된 batch price path를 재사용하는 편이 더 안전하기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: 성공

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 91개 테스트 통과

- 명령: `bash -n /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
- 관찰한 결과: 성공

- 명령: `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
- 관찰한 결과: 성공. Docker Postgres에서 `market.daily_price_bar=4`, `AAPL=2`, `BABA=2`, non-null `source_run_id=4`, succeeded `market_price_upsert` run 2건을 확인했다.

- 명령: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-universe-backfill`
- 관찰한 결과: 성공

- 명령: `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`
- 관찰한 결과: 출력 없음

## Still Unverified

- 항목: live Alpha Vantage universe backfill smoke
- 왜 중요한가: 현재 검증은 fixture 기준이라 실제 API rate limit과 live response shape는 별도 확인이 필요하다.

- 항목: strategy-specific universe slicing
- 왜 중요한가: 현재 canonical universe는 시장 전체 기준이고 실제 투자 전략 universe는 별도 계층이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: `strategy-universe-slicing`은 완료됐으므로 `market-feature-snapshot`으로 넘어가 strategy universe members의 deterministic market features를 계산한다.

## Risks

- 위험:
  - canonical universe가 아직 curated strategy universe는 아니다.
  - live Alpha Vantage rate limit/backoff는 없다.
  - backfill parent run abstraction이 없다.
- 대응:
  - 현재는 deterministic fixture-driven orchestration만 먼저 고정하고 운영 스케줄링은 후속 task로 분리한다.

## Useful Context

- 파일:
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/market/universe.py`
  - `src/stockanalysis/ingest/market/backfill.py`
  - `scripts/verify_market_price_universe_backfill.sh`
- 다시 찾기 싫은 배경지식:
  - canonical universe bootstrap sample은 `AAPL`, `BABA`를 active instrument로 생성하고 `BAESY`는 skip한다.
