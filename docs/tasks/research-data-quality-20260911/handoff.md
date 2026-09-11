# 인계 — 기업 보고서·수집 데이터 품질

## 완료 범위

현재 운영 데이터의 충분성을 감사하고 NVDA/AAPL/ARM 주요 주장과 무료 공식 원천을 대조했다. [감사 결과](report.md), [주장 기록](claims.md), [무료 수집 경로](free-sources.md)를 참고한다.

리서치의 연간 기간 선택 오류를 수정하고 비교군 미검증 범위를 입력에 추가했다. 세 보고서의 내용 hash에 검토 결과를 연결하여 기업 화면과 추천 상세에서 보완 항목·공식 링크를 보인다. 과거 보고서·재무 저장값·추천·benchmark·order 흐름은 유지한다. 신규 AI 호출은 없다.

로컬 코드·실제 PostgreSQL·운영 DB 읽기·Chrome 검증은 완료했다. 원격 CI와 운영 반영은 진행 후 아래에 기록한다.

## 이어갈 순서

1. 재무 기간/단위/source accession 보존과 ARM 비교연도·6-K, NVDA capex 처리. 기존 데이터 재적재는 별도 contract로 범위와 복구 방식을 정한다.
2. SEC/IR 원문 확보 및 활성 기업별 공시 갱신. EROK 차단은 최신 공시를 재평가한 후 판단한다.
3. FRED/ALFRED 장기·발표시점 이력과 빠진 고용/PCE/GDP, 가격/기업행동/ETF 관측 이력.
4. 보완된 입력 검증 후 필요한 AI 보고서만 다시 생성한다. 이번 인계는 새 호출 허가나 추천 weight 변경 승인이 아니다.

이전 news-source-consistency 작업의 04:00 UTC 정기 run에서 RSS upsert23838, event enrichment23840, translation23841가 succeeded로 관측됐다. 이전 인계의 '다음 정기 실행 미확인' 항목을 현재 감사에서는 확인했다. 원천 격리나 AI 호출을 재실행하지 않는다.

## 작업 경계

기존 다른 task 문서의 로컬 변경과 미추적 문서는 보존했다. 브랜치는 `fiture/research-data-quality-20260911`. 로컬 runtime/inventory/SEC 응답 스냅샷은 output에만 보관한다. 임시 PostgreSQL은 종료했고 Chrome 반응형 viewport는 원래 크기로 복구했다.
