# 검토

기존 cadence 선택 기준, feedback/calibration 계산, 데이터셋/평가 기준을 유지한다. 새 실행기는 완료된 child 뒤에 cadence를 다시 계산해 한 차례 실행 안에서 필요한 후속 작업을 이어 준다. 하루가 바뀔 때마다 feedback이 우선 선택되어 calibration이 누락되는 경로를 제거한다.

최대 child 2회, 동일 action 반복 금지, 실행 전후 cadence ID 비교, 실패 시 attention/비정상 종료를 적용했다. 기존 CLI 기본 동작은 단일 action이며 daily profile만 새 옵션을 명시한다. 정상 no-op도 기존 router에 남으므로 웹은 마지막 결정을 그대로 읽는다.

이 검토는 단일 에이전트 자체 검토다. 다른 호스트의 임의 수동 실행까지 원자적으로 잠그는 전역 lock은 도입하지 않았다. 운영 실행은 기존 단일 daily systemd 서비스와 타이머를 사용한다. 검토 결론을 자동 투자 결정으로 바꾸지 않는다.
