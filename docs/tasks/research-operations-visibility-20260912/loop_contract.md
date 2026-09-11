# 반복 운영 경계

Mac `im.stocka.web-tunnel` LaunchAgent: 로그인 시 SSH 시작, 연결 종료 시 30초 간격 재시작. 127.0.0.1:13309에서만 listen. ServerAlive 30초/3회. 키는 macOS Downloads 접근 제약 때문에 같은 Mac의 ~/.ssh/stocka-web.pem에 0600 복사. 원본/다른 키는 변경하지 않는다. AWS 규칙을 자동 확대하지 않는다. IP 변경 시 새 /32를 검증해 갱신해야 한다. 중지: launchctl bootout gui/$(id -u)/im.stocka.web-tunnel.

리서치 화면: 현재 worker의 execute=False 조회만 호출. 신규 예약·receipt 대조 갱신·AI 호출 없음. 오류는 unavailable과 null 예산으로 표시. source hash·raw config·시크릿·오류 원문은 반환하지 않는다. 자동 갱신의 기존 회당1개/UTC 하루5회/불명 결과 재호출 금지는 유지한다.

배치 복구: 기존 decision-daily 단위를 동일 자원 제한으로 1회 시작. 기존 자동 배치의 평가·페이퍼 snapshot 갱신은 복구 범위다. 알고리즘·weight·benchmark·실거래 경계 변경은 없다. 시작 체크포인트를 저장하고 중단/불명 결과는 저장 artifact부터 확인한다.
