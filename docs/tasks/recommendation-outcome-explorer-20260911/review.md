# Review

## 구현 경계

- 새 요청은 기존 FastAPI adapter와 read-token/method restriction 안에서 처리한다. 사용자 입력은 canonical parser로 제한하며 문자열은 SQL literal escaping을 사용하고 ID/limit는 bigint/integer 검증 후 삽입한다.
- 모든 SQL은 SELECT. schema, 추천/weight, benchmark, outcome 계산/평가 기준, AI invocation 변경 없음.
- 전체 저장 측정을 portfolio 귀속 조건 없이 조회한다. 통계는 필터 전체이며 페이지 크기와 다르다. 수익률 집계/평균/추천 결정은 만들지 않는다.
- 실제 horizon과 nominal ±7일을 구분한다. null benchmark/alpha와 0을 구분한다. 추천과 thesis는 현재 저장값이고 보존본은 평가 시점이라는 한계를 화면/계약에 설명한다.
- snapshot link는 recommendation calibration family + source outcome ID + source recommendation ID가 모두 일치할 때만 생성한다. bigint ID를 문자열로 유지한다.
- keyset은 종료일/ID 내림차순이며 insert ceiling을 다음 페이지에 전달한다. 기존 행의 향후 수정까지 고정하는 transaction snapshot은 아니다.
- 조건 초기화/최신 기록 재조회는 native navigation으로 새 요청을 보장한다. 필터별 native GET URL은 복사·새로고침·뒤로가기가 가능하다.

## 검토 결과

단위/실제 DB, 전체 CI와 운영 API/Chrome 검증을 완료했다. 확인 범위에서 미해결 기능 결함은 없다. 보존본 부재, 누락 benchmark, 평가 시점과 추천 생성 시점 차이는 알려진 데이터 한계다.

운영 조회1233행이 DB와 일치했고 보호 대상 테이블 전체 hash가 같았다. 운영 코드와 Linux artifact의 runtime 입력 일치, 환경/모델 설정 보존, 서비스 및 timer 복구를 확인했다. 실제 조회·상세 연결·미측정·빈 결과·invalid 상태가 검증돼 이번 contract 완료 기준을 충족한다.
