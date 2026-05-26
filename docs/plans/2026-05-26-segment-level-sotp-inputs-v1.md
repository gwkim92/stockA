# segment-level-sotp-inputs-v1 Plan

## Summary

- 목표는 reported segment evidence를 SOTP의 명시적 입력으로 끌어올리는 것이다.
- 이번 slice는 valuation math를 크게 바꾸지 않는다. 사업부별 revenue, operating income, operating margin을 근거로 보여주고, 실제 segment-level valuation weighting은 다음 task로 남긴다.
- 추천 weight, paper/broker/order boundary, benchmark, portfolio guardrail은 변경하지 않는다.

## Implementation Plan

1. `sum-of-parts-valuation-run` SQL에 `reported_segment_inputs` CTE를 추가한다.
2. `segment_evidence_inputs`가 reported segment input JSON을 집계하도록 확장한다.
3. `segment_data_gap_reserve` component assumptions와 valuation snapshot assumptions에 `reported_segment_inputs`를 저장한다.
4. live adapter가 `reported_segment_inputs`를 normalizing해서 DTO로 노출한다.
5. Next 타입과 valuation card가 한국어로 사업부별 매출, 영업이익, 영업마진, 기준 기간을 보여준다.
6. unit/frontend tests와 roadmap/AWH verification을 갱신한다.
7. EC2에서 SOTP/valuation snapshot을 재실행하고 API/route smoke로 실제 AAPL segment input이 보이는지 확인한다.

## Quality Bar

- 데이터가 없으면 기존 공백 표현이 유지되어야 한다.
- 데이터가 있으면 `사업부별 데이터 공백`만 반복하지 않고 실제 segment input list가 먼저 보여야 한다.
- 이번 작업은 investment recommendation 결과를 변경하지 않는다.
