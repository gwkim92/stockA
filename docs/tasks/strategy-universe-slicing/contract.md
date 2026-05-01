# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: strategy-universe-slicing
- 요청: canonical universe와 price bars를 이용해 중장기 전략용 universe snapshot을 생성하는 경로를 구현한다.
- 담당: Codex
- 날짜: 2026-04-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `strategy-universe-slice` CLI가 active canonical instruments 중 가격 데이터가 충분한 종목을 골라 `signal.strategy_universe_batch`, `signal.strategy_universe_member`에 저장한다.

## Why

- 이 작업이 제품이나 시스템에 중요한 이유: canonical market universe 전체를 바로 추천 후보로 쓰면 너무 넓다. recommendation 이전에 전략별 investable universe snapshot을 저장해야 이후 feature, cycle, thesis, recommendation이 같은 기준으로 재현 가능해진다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/ingest/market/backfill.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
- 관련 문서:
  - `docs/market-universe-bootstrap.md`
  - `docs/market-price-universe-backfill.md`
  - `docs/verification-plan.md`
- 이전 결정:
  - canonical universe는 `ref.issuer`, `ref.instrument`에 있다.
  - price availability는 `market.daily_price_bar`에서 확인한다.
  - recommendation은 아직 구현하지 않고 universe snapshot을 먼저 저장한다.

## Scope

- 포함:
  - strategy universe batch/member schema
  - active instrument + exchange + price data availability filter
  - minimum observation count, minimum adjusted close, limit
  - CLI, tests, docker verify, task docs
  - AI role map 문서
- 제외:
  - cycle score
  - theme/sector enrichment
  - AI-based ranking
  - live scheduling/retry
  - recommendation generation

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0004_strategy_universe.sql`
  - `docs/ai-role-map.md`
  - `docs/plans/2026-04-23-strategy-universe-slicing.md`
  - `docs/strategy-universe-slicing.md`
  - `docs/tasks/market-price-universe-backfill/handoff.md`
  - `docs/tasks/strategy-universe-slicing/`
  - `docs/verification-plan.md`
  - `scripts/verify_strategy_universe_slicing.sh`
  - `src/stockanalysis/signal/`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_strategy_universe.py`
  - `tests/test_ingest_cli.py`
- 수정 금지 파일:
  - existing market price upsert logic
  - SEC event/companyfacts logic
  - portfolio/recommendation logic
- 검증에 사용할 명령:
  - `bash /Users/woody/ai/stockanalysis/scripts/verify_strategy_universe_slicing.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task strategy-universe-slicing`
  - `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0004_strategy_universe.sql`
  - `docs/strategy-universe-slicing.md`
  - `docs/ai-role-map.md`
  - `docs/tasks/strategy-universe-slicing/contract.md`
  - `docs/tasks/strategy-universe-slicing/plan.md`
  - `docs/tasks/strategy-universe-slicing/handoff.md`
  - `scripts/verify_strategy_universe_slicing.sh`
  - `src/stockanalysis/signal/universe.py`
  - `tests/test_strategy_universe.py`
- 선택 결과물:
  - `docs/tasks/strategy-universe-slicing/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] strategy universe snapshot이 실제 DB에 저장된다
- [x] AI 역할이 프로젝트 전체 구조 안에서 문서화된다

## Verification Plan

- 자동 검증: `bash scripts/verify_strategy_universe_slicing.sh`, `awh verify --task strategy-universe-slicing`, placeholder 검색
- 수동 검증: `docs/ai-role-map.md`가 AI를 추천 결정자가 아니라 intelligence/report layer로 배치하는지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: unit/integration 검증 통과, strategy universe batch/member rows 생성 확인, readiness 검증 통과

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `strategy-universe-slice` command, signal universe runner, migration 0004를 제거하면 이전 market pipeline 상태로 복귀한다.

## Open Questions

- 질문: 이후 strategy universe가 sector/theme/cycle score를 언제 포함할지
- 답이 없을 때 적용할 임시 가정: 현재는 price availability와 단순 investability filter만 사용한다.
