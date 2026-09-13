# 재무 원천 대기와 평가 근거 후속

실행 요청: 이전 복구 이후 남은 자동화와 원천 자료 대기 해소를 계속한다.

현재 개인 EC2 develop4f68c091에서 원천 대기는 18→3(AAPL/ARM/NVDA), 버전 일치 보고서는2→10으로 자동 진척했다. 세 종목은 legacy sec_companyfacts_upsert/normalization 성공을 maintenance가 fresh로 보지만 보고서 실행기는 source SHA와 atomic maintenance receipt가 없어서 waiting_for_source로 본다. 동일 자료를 최신이라고 추정 연결하지 않고 기존 제한된 수집을 통해 검증 가능한 receipt를 만들게 한다.

범위: maintenance의 성공 원천 기준을 보고서와 공유, 실제 PG 회귀검증, CI/develop 배포, 기존 3개 이하 무료 SEC 수집 실행, 반복 no-op, 실제 대기열 및 보호 데이터 확인. 최신 성과평가의 needs_more_data 원인을 현재 DB로 조사해 다음 수집 작업의 구체적 대상을 기록한다.

한도/원천 기간 정책/평가 계산/schema/benchmark/추천 weight/모델 설정/실거래 경계를 변경하지 않는다. EROK 기존 전문 판단 차단은 유지한다. 보고서 추가 생성은 기존 한도와 자동 주기에 맡긴다. 외부 알림을 보내지 않는다. 서버 빌드·AWS 설정 변경은 없다.

완료: 테스트/CI 통과, 운영 source receipt 확인 및 원천 대기3개 해소 또는 구체적 실제 source blocker 기록, 기존 queue fresh/실행 제한 유지, 평가 결측 진단, task handoff.
