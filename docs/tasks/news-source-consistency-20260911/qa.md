# 검증

- 재현: query-only GUID `?src=A00220&yptr=yahoo`는 서로 다른 기사에 같은 `a9942e6ecc582301998de621` ID를 부여했다. 수정 전 3개 재현 검사가 실패했다.
- 실제 Yahoo RSS 47개 비교: 정상 ID 46개 유지, 충돌 GUID 1개만 기사 URL 기준으로 변경. 반복 수집과 기능성 query parameter 보존을 검사했다.
- 로컬 backend 관련 212개 통과. source DTO는 원제와 문서 ID를 보존하고 충돌 상태에서 번역/발췌/종목을 내보내지 않는다.
- 전용 PostgreSQL 17 포트 55488의 실제 migration 기반 4개 통과: 서로 다른 기사와 멱등 수집, 격리 전 기록 보존, 재실행 no-op, stale preview 원자적 실패, 복수 원천 이벤트 거부.
- 원천 reader 검증 56개 통과, Next typecheck/build 통과.
- 결과 파일: output/news-source-consistency-20260911/. 운영 적용과 Chrome 증거는 인계에 별도 기록한다.
