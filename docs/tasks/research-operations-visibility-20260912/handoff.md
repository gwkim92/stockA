# 완료 인계

접속 복구와 운영 화면 배포 완료. PR66, 배포 `ba63c79cdbb1fcc75a67673975f315dbce8948cf`, Linux build `7b4tP9Y3GJ9J_hfn1a-5s`. 현재 기능 기준 및 실제 증거는 qa.md와 evidence/verification.json에 있다.

개인 AWS 115623963546의 SSH 기존 단일 규칙 source만 14.32.108.104/32로 갱신했다. 포트 확대는 없었다. `im.stocka.web-tunnel` LaunchAgent로 http://127.0.0.1:13309/data-health 접속이 유지되며 프로세스 종료 후 자동 복구도 확인했다. 키는 같은 사용자 ~/.ssh/stocka-web.pem에 0600으로 복사했다. 원래 Downloads 키를 launchd에서 직접 사용하면 macOS TCC에 막혔다. 앞으로 외부 IP가 바뀌면 좁은 /32 규칙의 재확인이 필요하다.

운영 화면에 기업별 갱신 상태, 처리 이유, 재무 자료 시각, 실행 기록, 설정 모델, 일일 사용량/초기화 시각, 검색/필터와 모델 설정 링크를 추가했다. 실제 worker의 execute=False 계획을 읽고 GET에서 새 실행·AI 호출·reconcile을 만들지 않는다. 최신 시점 33개: current2/due13/source-wait18, quota2/5. 생성 대상은 기존 자동 주기에 처리되며 화면 클릭으로 생성하지 않는다.

이전 decision-daily는 equity 보고서5개 input_budget_exceeded 실패로 중단돼 있었다. 앞선 배포에서 보고서1개/마지막 단계 처리가 반영된 상태로 기존 service를 재실행해 23/23 성공을 확인했다. 모델 환경/SQLite, 자원 제한과 14개 timer를 보존했다. 데이터·투자 검토 경고 전체가 해소된 것은 아니다.

후속: feedback 이후 calibration이 다음 날짜에도 밀리는 실제 자동화 누락을 발견해 별도 `feedback-followup-20260912` task/PR67로 분리했다. 해당 인계가 성과 평가의 최신 상태를 설명한다. 추천 weight/benchmark/실주문 변경은 없다.
