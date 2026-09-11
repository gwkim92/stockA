# 운영 조회 계약

기존 인증된 GET /api/data-health 응답에 선택 필드 data.research_refresh를 추가한다. 기존 응답 버전과 필드는 유지한다. live adapter에서 현재 자동 worker의 execute=False 경로를 사용하며 별도 실행 API를 열지 않는다.

- status: loaded / attention_required / unavailable. 조회 실패 시 daily_used, daily_limit, daily_remaining, total_count, attention_count는 null이다.
- observed_at / as_of_date / budget_resets_at: UTC 조회 시각, UTC 예산 날짜, 다음 UTC 자정. 시장 자료의 as_of_date와 분리한다.
- model_name: worker가 동일 시점 설정에서 선택할 모델. 마지막 실제 서빙 모델은 기존 AI 운영 화면을 따른다.
- daily_used / daily_limit / daily_remaining: 기존 worker가 계산한 예약/수동 기록 합계, 기존5회 한도, 0 아래로 내려가지 않는 잔여량. 별도 수동 CLI를 전역 잠금으로 막는다는 의미는 아니다.
- counts / rows / total_count / attention_count: 전체 대상의 정확한 상태별 합계. 상태는 current, due, waiting_for_source, retry_wait, reconcile, attempt_recorded, result_changed. 알 수 없는 상태는 unknown으로 주의 분류한다.
- rows: symbol, state, source_run_id, source_collected_at, claim_id, retry_after, 정해진 failure_code만 공개. 원문 오류, 설정 JSON, 해시, 시크릿, 내부 경로를 제외한다.
- scope=financial_source_only / read_only=true / maximum_calls_per_run=1: 재무 입력 갱신에 한정한다. 호출이나 예약을 실행하지 않는다.

confirmed fallback은 저장된 ended_at+24h 이후 재시도 가능하며, 불명 결과/실패 확인 필요 상태는 자동 재호출하지 않는다. 대조는 기존 worker 실행 때 처리하며 페이지 조회가 상태를 고치지 않는다. 예산이 소진돼도 개별 due 상태는 유지하고 화면에서 다음 예산/스케줄 대기를 설명한다.
