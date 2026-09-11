# Handoff — 구현·운영 검증 완료

2026-09-11, PR #56: https://github.com/gwkim92/stockA/pull/56

## 제공 기능

사이드바 **판단 성과 → 전체 추천 성과**, `/performance/recommendations`. 저장된 추천 성과를 보유/귀속 보고서 조건 없이 종목·추천일·관찰 구간·벤치마크·초과수익으로 조회한다. 실제 측정일/수익률과 현재 추천 기록, 연결 투자 논리, 해당 성과를 사용한 평가 보존본을 연결한다. 기존 `/performance` 보유 성과귀속과 평가 이력은 유지한다.

사용 중인 운영 접속 주소: http://127.0.0.1:13309/performance/recommendations

## 코드·배포 증거

- 기능/검증 commits: `5fc25815`, `2cb086c3`, `364aa897`.
- develop 병합 및 운영 활성화 commit: `2ff9e398adf8076d74f3e46c34c5bed566acc65b`.
- 최종 PR CI 3개 성공. 전체 Web Product Quality run `34554185266` 성공. 앞선 안내 문구 기대값 실패는 기존 문구에 맞춰 수정했고 새 실행에서 전체 통과했다.
- Linux artifact run `34554197956`, source `364aa897efe71d13649b19ff9e3c096aae35a7c9`, BUILD_ID `kyqUydhqwNJjuslahjCFT`, SHA256 `45f3fa2e37dc015c74909c4ec73cc6ffc1dc6dd94e6a79be7a0ee52050c16f5a`.
- 개인 AWS `115623963546` / `i-029d51b163fb07b61` / us-east-1에서 identity 확인 후 기존 develop만 fast-forward. API ready=ok, web3000/13000 정상, 서비스3개 활성 및 기존 timer13개 복구.
- runtime env fingerprint 일치. AI 설정 revision2 / `gpt-5.6-terra` / overrides={} 유지. DB migration, 새 AI 호출, 금융 데이터 write 없음.

## 운영 데이터·사용자 흐름

- API 100행씩 13페이지의 1233개 outcome ID가 DB와 순서까지 일치. 중복0. 추천920개, 종목30개, alpha 미측정34건, 추천일2026-05-21~2026-08-11.
- 독립 DB 대조: AAPL54, 30일963, 90일208, 그 외62, benchmark/alpha 미기록34, alpha=0은96, positive453, negative650. 날짜 필터와 없는 종목0건 일치.
- 조회 전후 추천1358, score component32593, position515, benchmark composition612, outcome1233의 count와 row hash 전체 일치.
- snapshot2239 → recommendation1057/outcome1583 정확히 연결, integrity=verified. 미인증401, invalid/중복 query400.
- 실제 Chrome의 운영13309에서 AAPL 복합 필터, 초기화, 다음 페이지 중복0, through 유지, 모바일 overflow0 확인. 추천1057·thesis35·eval1755 보존본 실제 이동 및 빈 결과/invalid 화면 확인.
- 새 화면은 320/390/768/1440px에서 WCAG A/AA 자동검사 위반0, 가로 넘침0. 단위/빌드와 전체 기존 화면 CI도 통과했다.

## 증거 위치와 복구

- 로컬: `output/recommendation-outcome-explorer-20260911/`의 `activation.json`, `verification.json`, `pr-checks.json`, `pr-merge.json`, `production-browser-filter.log`, `production-browser-links.log`, `build-manifest.json`.
- 캡처: `output/playwright/outcome-explorer-production-desktop.png`, `outcome-explorer-production-mobile-results.png`, `outcome-explorer-production-snapshot.png`.
- 운영 receipt: `/opt/stockanalysis/runtime/recommendation-outcome-explorer-20260911/activation.json`, `verification.json`. 이전 source archive와 `previous-next` 보존. activation은 재실행하지 않는다.
- 임시 PostgreSQL55489는 종료했다. 로컬13329/18789는 읽기 전용 검증 preview이며 운영 증거와 구분한다.

## 남는 데이터 경계

전체 *저장 측정*을 조회한다. 아직 outcome이 없는 추천은 이 목록에 생성하지 않는다. 30/90/180/365일 ±7일 분류는 기존 평가 helper를 재사용하며 원시 관찰 기간을 함께 표시한다. 누락 benchmark/alpha는 미측정으로 남긴다. 현재 추천/thesis와 평가 실행 시점 보존본을 구분하며, 추천 생성 당시 불변 사본이나 실계좌 손익으로 간주하지 않는다. ID ceiling은 신규 insert를 제외하는 페이지 범위이며 기존 행의 미래 수정까지 동결하는 스냅샷은 아니다.

추천 weight, benchmark, 평가 기준, 실거래 경계를 변경하지 않았다. 원래 다른 task의 dirty/untracked 문서는 보존했다.
