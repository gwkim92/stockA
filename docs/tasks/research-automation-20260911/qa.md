# 검증

- 로컬 PostgreSQL 및 Python 회귀: 140개 통과. 원자적 원천/정규화/완료 기록, 변경 전 백업, 중간 실패 rollback, 실행 중 행 잠금, 중단 후 대조, 큐 최신성/구정책/24시간 대기, AI 순환·당일 건 제외·5개 예약 한도 포함.
- CLI·frontend read adapter: 214개 통과.
- Frontend API contract script 통과.
- Next typecheck/build 및 실행 이력 컴포넌트 2개 검사 통과.
- 운영 읽기 전용 preview: 개인 계정/instance 확인, 추적 기업 32개, 갱신 대상 29개, 정상 정책 3개. 새 data-health SQL 정상. AI 보고서 5개 입력 준비/preview 모두 정상, 실제 모델 호출 0회.
- 운영 배포·실제 반복 실행·Chrome 화면 검증: 진행 중. 완료 후 증거를 추가한다.
