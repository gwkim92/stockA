# 검증

- 실제 SEC 표본: tests/fixtures/sec_financial_periods_observed.json. 2026-09-11 관측 원문의 선택 concept과 filed cutoff를 그대로 보존했다. 테스트용 가공 숫자가 아니다.
- Python 관련 검사 88개 통과. CLI 검사는 별도 로그 참조.
- PostgreSQL 17 임시 instance에서 실제 migration의 financial table DDL로 4개 통합 검사 통과: ARM 성장률, AAPL/NVDA 분기 cash flow 제외, 기존 YTD 제거와 ID/다른 metric 보존, 실패 시 rollback, 공시일 cutoff와 종목 제한.
- scripts/verify_financial_period_integrity.sh: 초기 검증 70개 통과, 생성한 임시 DB 종료 확인.
- Linux CI 및 운영 적용: 아직 진행 전. 완료 후 갱신한다.
- 운영 전체 재무 행의 로컬 반출은 자동 승인 검토가 거부하여 수행하지 않았다. 이후 운영 대조/백업은 서버 내부에서만 수행하고 집계 결과만 반환한다.
