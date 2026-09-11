# 검토

- 실패 원인: 공시 fy/fp를 비교값 자체의 회계연도로 저장했고, SQL이 종료일별 min(start)와 최신 metric을 섞었다. 고정 행 수 chunk는 같은 기간을 둘로 나눌 수도 있었다.
- 수정은 원천 선택 및 정규화 SQL에 한정한다. 새 schema 없이 ops.pipeline_run.config_json에 선택 원문과 제외 사유를 남긴다.
- 회계연도는 동일 accession의 최신 정상 기간을 기준으로 52/53주 연도 간격을 확인한다. SEC calendar frame을 fiscal year로 사용하지 않는다. 범위를 벗어나는 변경 회계연도/비정상 기간은 제외한다.
- 최신 공시 하나, 동일 start/end의 duration 및 같은 종료일의 instant만 결합한다. 최신 공시에 없는 balance sheet 등은 과거 공시에서 채우지 않으므로 커버리지가 줄 수 있다.
- 검증된 기간만 기존 SEC 지원 metric을 원자적으로 교체한다. 사용자 정의 metric과 다른 종목, period ID는 보존한다.
- 분기 cash flow가 YTD이면 제외하고 차감 추정하지 않는다. 6-K와 NVDA productive-assets capex alias는 별도 지원 작업으로 남긴다.
- 과거 normalized snapshot과 추천/성과/보고서는 다시 쓰지 않는다. 새 normalization은 알려진 공시일과 정상 기간 범위를 요구하며 --symbol로 제한한다.
- 단일 에이전트 코드 검토이며 독립 검토자 승인을 주장하지 않는다. 실제 DB 및 CI 결과는 qa.md에 기록한다.
