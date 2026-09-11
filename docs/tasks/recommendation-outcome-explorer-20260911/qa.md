# QA — 2026-09-11

## 완료한 검사

- Frontend: 전체 43파일 / 529테스트 통과. 필터 입력과 URL, 정렬/커서/ID ceiling, 응답 범위 일치, 0/NULL, 인증 헤더/오류/timeout, 추천·thesis·snapshot 링크 검사 포함. 접근성 이름/초기화 수정 후 영향 테스트와 production build 재통과.
- Python: 새 API 단위 5개, 기존 adapter 포함 24개, history/API server 포함 50개 통과. 미인증 401 및 mutation method 405를 DB 접근 전 확인.
- 임시 실제 PostgreSQL: `stocka_outcome_explorer_test`, 포트 55489, 실제 migrations 0001/0002/0003/0005/0010/0035 적용. SELECT-only role + read-only transaction으로 4개 통합 시나리오 통과. 운영 DB와 분리.
- 기간 분류 23/37일→30일, 83/97일→90일, 0/1/22/38/98일→그 외. 기존 outcome window helper 재사용. 같은 종료일 paging 및 신규 backfill이 끼어들지 않는 ceiling 검증.
- `verify_frontend_api_contract.sh` 통과. v0.1 endpoint 계약은 유지하고 새 live-only 계약을 별도 절로 추가.
- 배포 전 새 모듈을 운영 호스트 메모리에서 읽기 전용으로 실행: 저장 측정 1233, 추천 920, 종목 30, alpha 미측정 34, 추천일 2026-05-21~2026-08-11. 근거: `output/recommendation-outcome-explorer-20260911/predeploy-live.json`.
- 실제 Chrome 로컬 preview: AAPL/추천일/30일/SPY/positive 조합 25행, 초기화 후 빈 조건, 다음 25행 중복 0, through 유지, 390px overflow 없음. `local-browser-filter.log`.

## 아직 남은 확인

최종 접기 가능한 필터의 렌더링, 관련 상세/평가 링크, 빈 결과/invalid 화면, Linux artifact/PR CI, 운영 활성화 후 실제 사용자 경로.
