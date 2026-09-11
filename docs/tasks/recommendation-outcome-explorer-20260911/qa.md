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

PR 전체 회귀 CI와 운영 활성화 후 실제 사용자 경로.

## 최종 로컬 브라우저

- 접기 가능한 필터에서 조회·초기화·페이지 이동을 다시 통과했다. 중단 후 남아 있던 프리뷰 프로세스의 출력 연결 문제로 API가 빈 응답을 내던 상황은 검증 서버 재시작으로 해소했다. 실제 화면은 조회 실패를 표시했고 0건으로 위장하지 않았다.
- SPY 추천1057 → 추천 상세 / thesis35 / eval1755 snapshot2239로 실제 클릭하여 이동. 보존본 첫 행 SPY, 점수0.5726, 30일, 종료일2026-09-10, 저장 내용 일치 확인. 없는종목 빈 결과와 역전 날짜 invalid 상태 확인. `local-browser-links.log`.
- Linux artifact run34552905016 success (commit5fc25815). 기존 E2E 메뉴 목적지/이름 기대값도 새 탐색 구조에 맞춰 갱신했다.

## CI 잔여 문구 회귀 수정

- run34553269626은 notebook/evaluation/home/holdings 검증을 통과한 뒤 기존 source reader의 안내 문구 기대값 2건에서 실패했다. base cfa3842에도 남아 있던 `저장된 한국어 요약이 없습니다`를 현재 제품 문구 `표시할 한국어 요약이 없습니다`로 맞췄다. 원제 보존·가짜 해석 금지 검증은 그대로 유지한다.
- 수정 후 readers 전체38, CI에서 skip된 company48, signals46개를 데스크톱/모바일 실제 브라우저에서 실행해 모두 통과했다. 제품 코드는 변경하지 않았다.
- 네 폭(320/390/768/1440)에서 새 페이지 WCAG A/AA 자동검사 위반0, 가로 넘침0. 실제 missing-alpha 표본 XOM에서 +7.25% 절대수익과 벤치마크/alpha 미측정이 분리됨을 확인했다.
