# 검증

로컬 실제 Postgres 포함 금융/자동화 회귀검사195개 통과. 신규 회귀검사는 legacy upsert+정규화 성공이 있어도 원천 해시/atomic receipt가 없으면 due임을 재현한다. 이후 running→reconcile, failed→retry_wait, hash 없는 성공→due, 유효 receipt→fresh를 확인했다. 기존 7일/24시간/ETF 제외 검증도 통과했다.

CI·운영 배포·3개 수집과 보호 데이터 대조는 진행 중이다.

## CI·운영 완료

PR69 Financial Period Integrity 통과. develop c13ffd43 배포 후 기존 worker로3개 수집(AAPL379/ARM41/NVDA400),84.020초/exit0. 원천대기0, 같은 상태 재실행 수집0. 보호 SQL9집합 hash/AI invocation41740/모델 설정 보존. 타이머14개 및13개 batch 보호 확인.

실제 데스크톱1440/모바일390 너비에서 HTTP200, 원천 대기0,3개 종목 검색/생성 대기·수집시각 확인, 가로 overflow 없음. 실제 캡처를 열어 확인했다. 애플리케이션 UI 코드는 변경하지 않아 기존 Linux build를 보존했으며 새 웹 빌드는 수행하지 않았다.

남은 경고와 평가 의미는 handoff.md 및 feedback-diagnosis.md에 명시했다. 회귀검사 통과를 투자 검증 통과로 해석하지 않는다.
