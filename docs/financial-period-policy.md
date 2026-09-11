# SEC 재무 기간 선택 정책

2026-09-11 `sec-statement-duration-v2`부터 적용한다. 구현은 `ingest/sec/financial_periods.py`, 저장은 기존 `financial_statement_period`, `financial_metric_value`, `ops.pipeline_run`을 사용한다. Schema 변경은 없다.

## 선택 규칙

SEC companyfacts의 `fy`/`fp`는 공시의 회계연도·분기다. 비교 기간 수치의 회계연도나 calendar frame의 연도와 같다고 가정하지 않는다. 같은 accession의 최신 정상 duration 종료일을 보고기간 기준으로 삼고, 각 비교 종료일이 연도 간격에 맞는지 확인하여 fiscal year를 정한다. 52/53주 차이를 허용하고 14일 이상 어긋나는 비교 기간은 제외한다.

- 지원 공시: 10-K, 20-F, 10-Q 및 수정 공시. 정상 연간 335~395일, 분기 75~110일 범위만 선택한다.
- 동일 scope/end에서 가장 최근에 공시한 단일 accession을 선택한다. 그 공시 안에서 start/end가 같은 매출·손익·현금흐름과 같은 종료일의 자산·부채 등 instant만 결합한다.
- 서로 다른 start, 동일 concept의 상충 값, 불명확한 fiscal quarter, 미확인 filed, 무한대/NaN은 제외한다.
- 주식 수만 있는 표지 날짜는 재무 기간을 만들지 않는다. 기간 평균 주식 수를 종료일 주식 수로 취급하지 않는다.
- 6/9개월 누적 cash flow를 분기 revenue와 나누지 않는다. 현재 구현은 독립 분기 cash flow를 타 공시와 차감해 추정하지 않는다.
- 최신 공시에서 빠진 이전 balance sheet를 다른 공시로 채우지 않는다. 따라서 일부 과거 기간의 지표 수가 줄 수 있다. 추후 교차 공시 호환성을 검증하는 별도 정책이 필요하다.

## 저장과 시점

채택한 원문의 concept, namespace, unit, start/end, accession, filed, fy/fp, frame, 값과 fiscal year 선택 근거는 실행의 `config_json.selected_facts`에 남긴다. 제외한 각 concept/기간의 가장 최근 관측과 이유는 `excluded_facts`에 남긴다. 전체 원문 revision archive나 완전한 point-in-time 저장을 대체하지는 않는다.

검증된 기간의 SEC 지원 metric은 한 transaction 안에서 교체한다. 새 선택에 없는 기존 누적 수치는 제거하고, period ID와 사용자 정의 metric은 보존한다. Chunk 경계가 기간을 나누지 않는다. 새 공시에 대응하는 source document가 없으면 이전 공시 링크를 재사용하지 않으며 정확한 accession은 실행 이력에 남는다.

정규화 v2는 `period_end`와 알려진 `report_date`가 기준일 이하인 정상 기간만 사용한다. `--symbol`을 반복해 적용 종목을 제한할 수 있다. 현재 raw 테이블은 최신 선택을 저장하므로 과거 당시 revision을 복원하는 기능은 별도로 필요하다. 이번 운영 교정은 오늘자 새 스냅샷을 생성하고 과거 정규화·AI 보고서·추천·성과를 보존했다.

공식 규격: [SEC EDGAR API](https://www.sec.gov/search-filings/edgar-application-programming-interfaces). 운영 증거와 재실행 경계는 [작업 인계](tasks/financial-period-integrity-20260911/handoff.md)를 따른다.
