# 검증

- 실제 SEC 표본: tests/fixtures/sec_financial_periods_observed.json. 2026-09-11 관측 원문의 선택 concept과 filed cutoff를 그대로 보존했다. 테스트용 가공 숫자가 아니다.
- Python 관련 검사 88개 및 CLI 검사 156개 통과. 이후 상충 값·새 공시 링크 검사를 추가했다. CLI의 임시 HTTPError ResourceWarning은 실패 없이 끝났으며 운영 호출 결과가 아니다.
- PostgreSQL 17 임시 instance에서 실제 migration의 financial table DDL로 5개 통합 검사 통과: ARM 성장률, AAPL/NVDA 분기 cash flow 제외, 기존 YTD 제거와 ID/다른 metric 보존, 실패 시 rollback, 공시일 cutoff와 종목 제한, 오래된 문서 링크 재사용 방지.
- scripts/verify_financial_period_integrity.sh: 최종 72개 통과, 생성한 임시 DB 종료 확인.
- Linux CI: [34568833271](https://github.com/gwkim92/stockA/actions/runs/34568833271) 72개 통과. 최종 PR head 43621aaf도 [34569058246](https://github.com/gwkim92/stockA/actions/runs/34569058246) SUCCESS 확인 후 PR #60 병합했다.
- 운영 commit `6b019ff344b9f53cbb7b28caf0b949a90d883586`, 개인 계정 115623963546 / i-029d51b163fb07b61 확인. 백엔드만 갱신했고 기존 Next build, 환경 설정, schema는 유지했다.
- 실제 import ARM 23861 / 41 facts, AAPL 23862 / 379 facts, NVDA 23863 / 400 facts. 정규화 23864. 입력 증거는 해당 run config_json, 교정 전 DB 행은 같은 EC2의 비공개 task backup에 보존했다.
- 운영 SQL 검사: ARM FY2026 매출 성장률 computed, AAPL 2026-06-27 및 NVDA 2026-07-26의 분기 operating_cash_flow_margin unavailable/null. 다른 종목 raw/period와 모든 이전 normalized, 추천/점수/보유/benchmark/성과/AI 보고서의 해시 불변 확인.
- 운영 API 검사 2026-09-11T06:18:31Z: ARM 2026-03-31 / 13 computed, AAPL 2025-09-27 / 13, NVDA 2026-01-25 / 10. 정규화 기준일은 모두 2026-09-11. 실제 AI 입력 SELECT도 같은 annual period를 선택한다. 새 AI 호출 없음.
- 기존 보고서 494/493/492와 원천 검토 보완 필요 상태 유지. 서비스 3개 active, 원래 활성 타이머 13개 active 복원 확인.
- 실제 Chrome 127.0.0.1:13309의 세 기업 재무·가치 탭을 열고 수치를 확인했다. ARM 성장률 22.79%, AAPL 6.43%, NVDA 65.47%; NVDA 미제공 capex/FCF/ROIC도 그대로 표시된다.
- 캡처와 로컬 요약 증거: `output/financial-period-integrity-20260911/{arm-financial-desktop.png,aapl-financial-desktop.png,nvda-financial-desktop.png,verification.json,pilot-result.log,ci-tests.log,full-validation.log,cli-tests.log}`. 이번 UI 구조 변경은 없어 모바일 재검사는 하지 않았다.
- 운영 전체 재무 행의 로컬 반출은 자동 승인 검토가 거부하여 수행하지 않았다. 이후 운영 대조/백업은 서버 내부에서만 수행하고 집계 결과만 반환한다.
- CI 진행 중 상태에서 병합을 묶은 명령도 자동 검토에서 거부됐다. 이후 최종 head의 COMPLETED/SUCCESS와 CLEAN을 별도 조회하여 확인한 뒤 동일 head 제한으로 병합했다. 미해결 승인 차단은 없다.
