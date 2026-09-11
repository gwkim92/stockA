# 실행 계획

1. 버전·예약 SQL: 기존 ops.pipeline_run JSON metadata에서 성공한 재무 원천 버전, 이전 생성 예약, 사용한 하루 한도를 읽는다. 예약은 하나의 짧은 DB transaction 안에서 경합을 직렬화한다.
2. 생성·저장 연결: equity context와 batch 입력 manifest에 원천 버전을 기록하고 기존 result receipt로 저장 결과를 검증한다. 원천 교체 후 읽는 화면은 현재 버전과 비교한다.
3. 자동 실행과 화면: research-maintenance 후단 및 기존 daily reporting을 같은 제한된 runner로 연결한다. 기업 리서치 생성 경로에 재무 버전 상태를 표시한다.
4. 검증: fake provider와 전용 disposable Postgres에서 실패·경합·중복·quota·원천 변경을 확인하고 기존 AI/CLI/API/브라우저 회귀를 실행한다.
5. 배포·인계: develop/CI artifact 검증, private 백업, 기존 resource guard·14 timers 유지, 실제 max1 canary 후 같은 원천 no-op와 보호 데이터 hash 확인. 실서버에서 새 웹 build 금지.
