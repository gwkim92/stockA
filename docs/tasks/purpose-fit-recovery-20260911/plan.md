# 실행 순서

## 1. 성과 처리 원인과 복구

- operating_data_orchestrator의 daily/monthly 성과 명령 범위와 실제 저장된 router 필터를 대조한다.
- recommendation_outcome_backfill / sample audit / performance schedule이 같은 과거 추천·기간을 선택하는지 검증한다.
- 기존 가격·결과의 존재, 날짜와 표본 범위를 확인하고 bounded preview → 실행 → 재조회로 복구한다.
- 최신성·처리 대상 차이를 data-health가 설명하도록 한다.
- 관련 Python 테스트와 실제 Postgres 검증으로 신규·과거 유니버스, 미도래·처리완료·가격 누락을 다룬다.

## 2. 판단 상태와 데이터 의미

- frontend의 목록·상세 사용 경계를 공통 규칙으로 통일한다. 가상 검증 입력 자격과 성과 검증 완료를 분리한다.
- 가격 행의 존재를 fresh로 간주하는 기본값과 fundamental_quality의 다른 지표 대체를 없앤다.
- 기존 소비자와 UI의 unknown / pending / blocked 표현을 맞춘다.

## 3. 기업 리서치의 내용과 추적

- 실패한 기업 리서치 호출 원인과 컨텍스트·프롬프트·검증·fallback 경로를 확인한다.
- 주장별 근거, 기업별 검증 조건, 반대 근거를 지원하고 미충족을 사실대로 표시한다.
- 문장 개수 통과와 형식·근거·내용 검토의 상태를 구분한다.
- 기업·판단서에 실제 생성 모델·일시·대체 경로와 검토 수준을 표시하고 원천 접근을 연결한다.
- 제한된 대표 기업 표본으로 실제 성공 실행과 저장 내용을 확인한다.

## 4. 통합과 사용자 흐름

- Python 관련 검사, 프런트 단위/타입/build, 실제 desktop/mobile 흐름을 확인한다.
- 기존 develop 통합·CI·운영 배포 절차를 따른다. 배포 전 보호 데이터와 환경 불변성을 확인한다.
- 운영 목록→판단서→원천, 기업 보고서, 보유→성과, data-health 흐름을 다시 확인한다.
- qa.md, review.md, handoff.md에 증거·미검증 범위를 남긴다.
