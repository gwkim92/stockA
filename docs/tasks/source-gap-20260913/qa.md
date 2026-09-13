# 검증

로컬 실제 Postgres 포함 금융/자동화 회귀검사195개 통과. 신규 회귀검사는 legacy upsert+정규화 성공이 있어도 원천 해시/atomic receipt가 없으면 due임을 재현한다. 이후 running→reconcile, failed→retry_wait, hash 없는 성공→due, 유효 receipt→fresh를 확인했다. 기존 7일/24시간/ETF 제외 검증도 통과했다.

CI·운영 배포·3개 수집과 보호 데이터 대조는 진행 중이다.
