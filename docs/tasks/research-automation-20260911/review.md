# 변경 검토

- 재무 원천 변경 전 값은 동일 DB child run에 보존한다. Docker 내부 psql에서 호스트 경로로 COPY하지 않는다. 공개 SEC payload만 호스트 artifact에 저장한다.
- 변경 전 백업, SEC metadata/facts upsert, 해당 종목 현재일 정규화, 성공 receipt가 한 transaction이다. 완료 응답이 유실되어도 DB 행 잠금과 status로 판단한다.
- 이전 날짜 정규화와 추천/position/benchmark/weight/order SQL은 재무 runner에 없다. 원천 기간 교정 자체는 기존 sec-statement-duration-v2 규칙을 재사용한다.
- 같은 호스트의 worker lock과 DB 쓰기 잠금으로 중복 실행 및 기존 주간 writer와의 충돌을 제한한다. 다른 artifact root/다른 호스트의 임의 실행까지 분산 lock으로 지원하는 것은 이번 배포 범위가 아니다.
- AI 입력은 필수 identity를 유지한다. 긴 선택 항목은 문자열 중간을 자르지 않고 전체 레코드를 생략하며 생략 개수를 prompt와 결과에 남긴다. 필수 identity의 크기/형식 오류는 계속 차단한다.
- AI 자동 선택은 과거 active 추천 전체에서 미작성·오래된 보고서 우선이며, 당일 primary 보고서를 건너뛴다. 당일 pipeline에 예약된 symbols도 최대 5개 한도에 포함해 중단 뒤 무제한 재호출하지 않는다. 사용자가 명시한 종목 실행은 기존 CLI 동작을 유지한다.
- 일일 profile의 단계 실패 차단을 제거하지 않는다. 기업 보고서를 마지막에 배치하여 해당 작업 실패가 앞선 보유·성과 점검을 막지 않게 한다.
- 수집 신선도는 전체 내용의 정확성 증명이 아니다. 지원하지 않는 원천·보고서의 기존 검토 경계는 그대로 표시한다.
