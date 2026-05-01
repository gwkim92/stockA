# Session Handoff

이 문서는 장기 작업을 멈출 때 다음 세션이 바로 이어받도록 만드는 상태 스냅샷이다.

## Active Task

- 이름: market-feature-snapshot
- 담당: Codex
- 날짜: 2026-04-23

## Current Status

- 완료:
  - strategy universe members에 대한 deterministic market feature snapshot 경로를 구현했다.
  - feature definition schema와 instrument feature snapshot schema를 추가했다.
  - CLI, unit tests, Docker verify, 운영 문서를 추가했다.
  - AI path와 deterministic market path를 병렬로 이어가야 한다는 점을 task 문서에 남겼다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/plans/2026-04-23-market-feature-snapshot.md`
  - `docs/market-feature-snapshot.md`
  - `docs/tasks/market-feature-snapshot/contract.md`
  - `docs/tasks/market-feature-snapshot/plan.md`
  - `docs/tasks/market-feature-snapshot/handoff.md`
  - `docs/tasks/market-feature-snapshot/review.md`
  - `db/migrations/0006_market_feature_snapshot.sql`
  - `scripts/verify_market_feature_snapshot.sh`
  - `src/stockanalysis/signal/features.py`
  - `tests/test_market_feature_snapshot.py`
- 수정:
  - `README.md`
  - `docs/db-schema-design.md`
  - `docs/verification-plan.md`
  - `src/stockanalysis/signal/__init__.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_ingest_cli.py`
- 의도적으로 안 건드린 것:
  - existing market price upsert logic
  - existing strategy universe runner behavior
  - AI event extraction path
  - recommendation logic

## Decisions

- 결정:
  - `market-feature-snapshot`은 strategy universe snapshot을 입력으로 사용한다.
  - 초기 feature set은 deterministic bootstrap features만 둔다.
  - AI event path와 별개로 deterministic market path를 계속 이어간다.
- 이유:
  - recommendation chain이 strategy universe 다음 단계에서 끊기지 않아야 하기 때문이다.

## Verification Already Run

- 명령: `python3 -m compileall src tests`
- 관찰한 결과: 성공

- 명령: `PYTHONPATH=src python3 -m unittest tests.test_market_feature_snapshot tests.test_ingest_cli -v`
- 관찰한 결과: 새 feature snapshot unit/CLI tests 포함 28개 테스트 통과

- 명령: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- 관찰한 결과: 전체 114개 테스트 통과

- 명령: `bash -n scripts/verify_market_feature_snapshot.sh`
- 관찰한 결과: 성공

- 명령: `bash scripts/verify_market_feature_snapshot.sh`
- 관찰한 결과: 성공. Docker Postgres에서 feature definition 5건, feature row 10건, `AAPL latest_adjusted_close` 1건, `BABA return_1d` 1건, latest `market_feature_snapshot` run status `succeeded`를 확인했다.

## Still Unverified

- 항목: Docker Postgres에서 market feature snapshot end-to-end
- 왜 중요한가: unit test만으로는 strategy universe와 feature tables가 함께 연결되는지 증명할 수 없다.
- 항목: live market data smoke
- 왜 중요한가: 현재 검증은 fixture 기준이라 실제 Alpha Vantage response drift와 live rate limit은 별도 확인이 필요하다.

## Exact Next Step

- 다음 세션은 이것부터 시작: deterministic 축은 `cycle-state-snapshot` 또는 `recommendation-bootstrap`, AI 축은 `live OpenAI Responses provider`를 병렬 backlog로 유지한다. 둘 중 추천에 더 직접적인 다음 경계는 deterministic `cycle-state-snapshot`이다.

## Risks

- 위험:
  - bootstrap feature set은 간단해서 실제 투자 quality filter로는 부족하다.
  - classification/cycle-aware features는 아직 없다.
  - AI path와 deterministic path를 따로 유지해야 하므로 우선순위 관리가 필요하다.
  - feature rows는 `(instrument_id, as_of_date, feature_code)` pk라 같은 날짜 재계산 시 최신 값으로 덮어쓴다.
- 대응:
  - 현재는 deterministic snapshot boundary를 먼저 고정한다.
  - sector/theme/cycle features는 후속 task에서 붙인다.
  - AI와 deterministic task를 병렬 backlog로 관리한다.
  - methodology version은 `evidence_json.feature_set_version`과 `source_run_id`로 추적한다.

## Useful Context

- 파일:
  - `src/stockanalysis/signal/universe.py`
  - `docs/strategy-universe-slicing.md`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json`
  - `tests/fixtures/alpha_vantage_daily_adjusted_BABA.json`
- 다시 찾기 싫은 배경지식:
  - fixture universe는 `AAPL`, `BABA` 2개다.
  - 두 symbol 모두 2024-10-31, 2024-11-01 2개 adjusted close row가 있다.
