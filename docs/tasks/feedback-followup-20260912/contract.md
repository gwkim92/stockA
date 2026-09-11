# 성과 후속 평가 자동 완료

운영 증거: 2026-09-11 decision-daily 복구에서 feedback 실행은 성공했지만 cadence는 이전 feedback 기준 run_feedback_now 상태였고 calibration은 7월4일 eval697에 머물렀다. 기존 라우터는 feedback 후 다음 cadence를 기다리므로 일일 날짜가 바뀌면 다시 feedback을 먼저 선택해 calibration을 미룰 수 있다.

기존 backend action router에 opt-in --complete-follow-ups 실행 경계를 추가하고 daily profile에서 사용한다. fresh cadence → 안전한 기존 router → fresh cadence 순서를 최대3회 관찰해 feedback/calibration을 각각 최대1회 실행한 뒤 최종 no-op 상태를 남긴다. 같은 action 반복·선택 변경·child 미완료는 자동 반복하지 않고 attention/nonzero로 종료한다. 기존 단발 CLI는 유지한다. 동시 관리자 호출을 전역 잠금으로 막는 기능은 아니다.

수정 범위: maintenance backend, CLI 옵션, 기존 daily profile 연결, 회귀 검사. 신규 timer/schema/평가 기준/추천 weight/benchmark/portfolio position/실거래/AI 모델 호출 변경은 없다. 기존 결정과 모순은 최신 누적평가에 그대로 남긴다.

완료: 필요한 후속 단계의 같은 실행 내 완료·이미 최신이면 no-op·반복 방지·preview 무변경 검사, CI, develop 배포, 제한된 deterministic 운영 실행과 최신 cadence/calibration readback. task handoff에 저장한다.
