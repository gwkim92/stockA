# 진행 인계

maintenance가 legacy upsert+normalization만으로 fresh 처리하고 report worker는 atomic source receipt만 인정하던 불일치를 수정했다. latest_source_sql을 공유하여 해시/정책/성공시각 검증을 동일하게 적용한다. 기존 정상 receipt는 그대로 fresh이며 해시 없는 legacy 자료만 기존 3개 제한/7일 갱신/24시간 실패대기 흐름으로 보강한다.

최초 운영 상태: develop4f68c091, 계정115623963546, instancei-029d51b163fb07b61, batch13개 protected. 원천 대기 AAPL/ARM/NVDA, current10/due20. 이번 실제 배포·수집 결과는 아직 미확인이다. 평가 결측 진단을 함께 진행한다.
