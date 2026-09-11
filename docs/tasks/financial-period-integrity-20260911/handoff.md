# 재무 기간 무결성 인계

## 완료

2026-09-11 PR #60 병합 및 운영 적용 완료. 운영 소스는 `6b019ff344b9f53cbb7b28caf0b949a90d883586`; 구현 커밋 c61a7a20 / 3e0b82e8, 배포 절차 43621aaf. 웹 build는 이전 검증본 HdpZ5RuqCgm8IBu4chCvN을 유지한다.

SEC 공시 fy/fp를 과거 비교값에 그대로 붙이던 오류, quarter/YTD 혼용, cover-page shares 기간, chunk 분할, 새 공시의 과거 문서 링크 잔존을 수정했다. 원천 정책은 [financial-period-policy](../../financial-period-policy.md)에 기록했다. Schema, 추천 weight, benchmark, 주문, 모델 설정을 변경하지 않았다.

세 종목에서 총 153개 기간 / 820개 원천 값을 선택했다. fiscal year 교정 대상 141개, start 교정 71개, 호환되지 않는 기존 metric 제거 477개였다. 이는 재무 값이 사라진 원인을 숨기는 처리가 아니라 다른 duration/filing 또는 기간 평균 주식 수를 현재 statement와 혼합하지 않는 정책이다. 교정 전 값은 서버 내부에 보존했다.

- ARM import 23861: 41 facts. FY2026 연간 추가, 2026-03-31 기준 13개 계산, 매출 성장률 22.79%.
- AAPL import 23862: 379 facts. 2025-09-27 연간 13개 계산, 매출 성장률 6.43%.
- NVDA import 23863: 400 facts. 2026-01-25 연간 10개 계산, 매출 성장률 65.47%.
- 정규화 run 23864: 비어 있음을 확인한 2026-09-11 snapshot에만 생성. 과거 normalized와 다른 종목, 추천·보유·성과·보고서 보호 해시 불변.
- 분기 cash flow: AAPL 2026-06-27, NVDA 2026-07-26은 YTD만 있어 quarterly 비율 unavailable/null 확인. 독립 분기 추정은 하지 않았다.
- 운영 API / 실제 Chrome 세 화면 확인. 과거 AI 보고서와 보완 필요 상태 유지. 3 services / 원래 13 timers active.

## 증거와 재실행 금지

서버 `/opt/stockanalysis/runtime/financial-period-integrity-20260911/`의 `backend-activation.json`, `started.json`, `checkpoint.json`, `completed.json`, `verification.json`이 완료 증거다. `raw-before.json`, `protected-before.json`, `previous-source.tar.gz`는 같은 서버의 비공개 백업이다. 원본 DB 행을 로컬로 가져오지 않았다.

`activate_backend.py`와 `runtime_pilot.py --execute`는 이미 성공했다. 재실행하지 않는다. 다음 교정은 새 task와 현재 스냅샷/입력 범위를 정해 수행한다. 정상 동작은 기존 SEC 수집 runner와 financial-metric-normalization-run에 통합되어 있다.

로컬 `output/financial-period-integrity-20260911`에는 공개 SEC 원문, 테스트 로그, 변경 건수, 검증 결과, 화면 캡처만 있다. 브라우저는 기존 tunnel 13309를 사용했다. CI 72개와 CLI 156개 검사 통과; 자세한 범위는 qa.md를 따른다.

## 다음 작업

1. `6-K`의 실제 FY/Q 보고기간을 공식 문서로 확인해 ARM 분기 지원을 추가한다. 일반 6-K를 10-Q와 동일하게 취급하지 않는다.
2. NVDA `PaymentsToAcquireProductiveAssets`의 의미와 구성 항목을 검증하여 capex adapter를 확장한다. 현재 미제공 표시는 유지한다.
3. 공식 뉴스/정책 원문과 SEC 본문 수집, 관측·공시·효력 날짜와 원문 checksum 보존을 진행한다.
4. 오래된 종목부터 갱신하는 SEC 수집 순서와 나머지 기업의 구 raw 기간을 별도 bounded batch로 교정한다. 전체 종목의 기존 오염이 일괄 해결됐다고 주장하지 않는다.
5. FRED/ALFRED vintage와 장기 가격/배당 이력은 후속 단계다. 현재 저장 구조는 완전한 PIT revision을 보장하지 않는다.

기존 AI 보고서·사이드바 조건·peer/valuation snapshot은 이전 기준일의 기록이며 이번에 재생성하지 않았다. 특히 ARM 과거 보고서가 FY2025 수치만 언급하는 문구는 원본 보존 상태다. 최신 재무표와 보고서 기준일을 함께 읽어야 하며, 향후 새 보고서 생성 시 원천 대조가 다시 필요하다. 독립 분기 cash flow, ROIC, 일부 역사적 balance sheet, 6-K 및 전체 수집 범위의 부족을 남긴다.
