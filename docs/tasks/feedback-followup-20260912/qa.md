# 검증

- 실제 Postgres를 포함한 금융/자동화 회귀검사 194개 통과: `STOCKA_TEST_POSTGRES_BIN=/opt/homebrew/opt/postgresql@17/bin bash scripts/verify_financial_period_integrity.sh`.
- CLI/오케스트레이터/새 후속 실행기 125개 통과: `PYTHONPATH=src .venv/bin/python -m unittest tests.test_portfolio_review_feedback_maintenance tests.test_data_operations_cli tests.test_operating_data_orchestrator`.
- 새 실행기 9개 시나리오: feedback→calibration→no-op, 기존 feedback 이후 calibration만 실행, 같은 날짜 재실행 no-op, 반복 선택 중단, cadence 교체 중단, child 실패 중단, cadence 실패 중단, guardrail 차단, 미실행 preview/CLI attention 종료 코드. 첫 테스트는 완료 이후 재실행도 포함한다.
- 최초 제한 환경의 Postgres initdb는 macOS 공유 메모리 권한으로 실행되지 않았고, 임시 로컬 DB 실행 권한으로 재검사해 통과했다.
- 아직 CI/운영 반영/실제 calibration 완료 검증 전이다.

## CI/운영 완료

PR67 financial-period/batch-runtime 둘 다 통과. 77b6b327 운영 backend 반영. 상세 결과 evidence/verification.json.

- 실제 첫 실행 calibration23960/eval1771 완료 후 최종 cadence1773/router1774 no-op.
- 같은 날짜 반복 실행 cadence1775/router1776 no-op, child 미실행.
- 보호 대상9개 SQL 집합 전체 행 hash 불변, 모델 SQLite 불변, AI invocation41087 불변.
- 기존 웹 build/환경 설정 불변. transient service61.160초/exit0, 타이머14개 복원.
- 현재 calibration_current는 실행 최신성이다. 투자 누적평가 collect_more_feedback와 모순/원천 경고는 유지한다.
