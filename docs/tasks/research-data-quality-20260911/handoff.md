# 인계 — 기업 보고서·수집 데이터 품질

## 완료 범위

현재 운영 데이터의 충분성을 감사하고 NVDA/AAPL/ARM 주요 주장과 무료 공식 원천을 대조했다. [감사 결과](report.md), [주장 기록](claims.md), [무료 수집 경로](free-sources.md)를 참고한다.

리서치의 연간 기간 선택 오류를 수정하고 비교군 미검증 범위를 입력에 추가했다. 세 보고서의 내용 hash에 검토 결과를 연결하여 기업 화면과 추천 상세에서 보완 항목·공식 링크를 보인다. 과거 보고서·재무 저장값·추천·benchmark·order 흐름은 유지한다. 신규 AI 호출은 없다.

로컬 코드·실제 PostgreSQL·운영 DB 읽기·Chrome 및 원격 CI를 모두 통과했다. [PR58](https://github.com/gwkim92/stockA/pull/58) 병합 commit `aa87112503426c30e18e0917b2b8fd52ae54ca87`를 운영에 반영했다. BUILD_ID `HdpZ5RuqCgm8IBu4chCvN`, artifact source `2c2f44c9`. CI 34565086520(전체 화면), 34565086494(Python/실제 PostgreSQL), 34565086546(평가 이력), 34565112081(Linux 빌드) 성공.

운영 API/Chrome 13309에서 기업 3개와 추천1501의 검토 결과를 확인했다. 재무 입력은 NVDA2026-01-25 계산 가능9개, AAPL2025-09-27 12개, ARM2025-03-31 12개다. 읽기 검증 전후 9개 테이블 hash 불변, 환경/모델 설정 유지, timer13개 복구. 기존 보고서는 재생성하지 않았다. 검토/정규화 잔여 문제는 아래 작업에서 다룬다.

배포 영수증·복구본은 운영 `/opt/stockanalysis/runtime/research-data-quality-20260911/`에 있다. `activation.json` 존재 시 활성화 스크립트를 재실행하지 않는다. 로컬 증거는 `output/research-data-quality-20260911/activation.log`, `verification.json`, `production-browser.json`과 `production-aapl-*.png`다.

## 이어갈 순서

1. 재무 기간/단위/source accession 보존과 ARM 비교연도·6-K, NVDA capex 처리. 기존 데이터 재적재는 별도 contract로 범위와 복구 방식을 정한다.
2. SEC/IR 원문 확보 및 활성 기업별 공시 갱신. EROK 차단은 최신 공시를 재평가한 후 판단한다.
3. FRED/ALFRED 장기·발표시점 이력과 빠진 고용/PCE/GDP, 가격/기업행동/ETF 관측 이력.
4. 보완된 입력 검증 후 필요한 AI 보고서만 다시 생성한다. 이번 인계는 새 호출 허가나 추천 weight 변경 승인이 아니다.

이전 news-source-consistency 작업의 04:00 UTC 정기 run에서 RSS upsert23838, event enrichment23840, translation23841가 succeeded로 관측됐다. 이전 인계의 '다음 정기 실행 미확인' 항목을 현재 감사에서는 확인했다. 원천 격리나 AI 호출을 재실행하지 않는다.

## 작업 경계

기존 다른 task 문서의 로컬 변경과 미추적 문서는 보존했다. 구현 브랜치는 `fiture/research-data-quality-20260911`, 최종 인계는 `fiture/research-data-quality-evidence`에서 기록한다. 로컬 runtime/inventory/SEC/ALFRED 응답 스냅샷은 output에만 보관한다. 임시 PostgreSQL은 종료했고 Chrome 반응형 viewport는 원래 크기로 복구했다.
