# 검증 기록

## 로컬 코드·실데이터

- Python 관련 6개 모듈 160테스트 통과: content review, live adapter, purpose fit recovery, equity reporting, cutoff, equity contract v3.
- Frontend 전체 44파일 / 532테스트 통과. 마지막 접기 UI 수정 후 해당 컴포넌트 3테스트 재통과.
- Next.js typecheck 및 격리 production build 통과. 마지막 UI 수정 후 build 재통과.
- 임시 PostgreSQL 17에서 기존 시간대/cutoff 회귀와 새 4개 SQL 시나리오 통과: 주식 수 날짜 제외, 실제 최신 기간의 결측 유지, 미래/미상 보고일 제외, 비교군 미검증 표시. 전용 DB의 transaction 안에서 fixture를 만들고 rollback했다. 전용 클러스터는 종료했다.
- 수정된 실제 SELECT를 운영 DB에서 read-only로 실행: NVDA 2026-01-25, AAPL 2025-09-27, ARM 2025-03-31. 결과는 `corrected-contexts.json`에 보관.
- 공식 SEC companyfacts NVDA/AAPL/ARM 모두 조회 성공. 새 AI 호출·운영 DB 쓰기 없음.
- 기존 FRED 키로 UNRATE 2024-01/02의 두 vintage 조회 모두 200. 시점 지정 접근은 확인했지만 두 표본 값이 같아 수정 차이 사례까지 검증한 것은 아니다.

## 실제 Chrome

로컬 preview는 운영 API를 GET으로 읽고 실제 새 review adapter를 적용했다. 18790 API/13330 Next.js는 이번 작업 전용이며 운영 13309와 구분한다.

- AAPL desktop: 보완 상태가 기본 펼침, 세부 3항목은 접어서 표시. 실제 클릭으로 세부 펼침과 공식 Apple FY2025 원문 새 탭 이동 확인.
- AAPL/NVDA/ARM 390px: 각 기업의 맞는 검토 요약 표시. scrollWidth=clientWidth=390.
- 추천1501: 같은 AAPL 검토 결과 노출, 390px 넘침 없음, 브라우저 error 로그 0.
- 원 보고서 본문은 유지되고 검토가 전체 사실 인증/사람의 투자 승인이 아님을 표시한다. 미등록 보고서는 계속 미검토다.
- 캡처: `output/research-data-quality-20260911/aapl-desktop.png`, `aapl-mobile.png`, `arm-mobile.png`, `recommendation-desktop.png`. `local-browser.json`에 일부 DOM 검증 기록.

기존 Playwright 세션의 캡처는 시간 초과됐다. CUA의 새 Chrome 탭에서 최종 캡처를 확보했다. 첫 temp build의 node_modules symlink는 Turbopack root 제한에 걸렸으나 격리 경로에 로컬 dependency를 복사한 뒤 통과했다. 제품 의존성이나 설정은 변경하지 않았다.

## 운영 반영

- 최종 commit `2c2f44c96936bd8ed005e18e187a7d191f061f2a`의 [Web Product Quality 34565086520](https://github.com/gwkim92/stockA/actions/runs/34565086520) 전체 성공. notebook·평가 이력·홈·보유/성과·원문·기업·뉴스/테마 실제 브라우저 검사가 모두 통과했다. 접힌 상태의 안전하지 않은 링크 검사도 hidden DOM을 포함하도록 보강했다.
- [Analysis Prompt Quality 34565086494](https://github.com/gwkim92/stockA/actions/runs/34565086494): Python 3.11/3.13, 실제 PostgreSQL cutoff 및 atomic 검사 모두 성공. [Evaluation History 34565086546](https://github.com/gwkim92/stockA/actions/runs/34565086546)도 성공.
- [Linux artifact 34565112081](https://github.com/gwkim92/stockA/actions/runs/34565112081) 성공. BUILD_ID `HdpZ5RuqCgm8IBu4chCvN`, SHA-256 `e31c75d90d7d6e7f4ca249cdfa58c934e2b4b38e83b70dc82568aa29c2949425`.
- [PR 58](https://github.com/gwkim92/stockA/pull/58) 병합 후 운영 develop `aa87112503426c30e18e0917b2b8fd52ae54ca87` 활성화. 개인 계정/인스턴스 확인, API ready=ok, 서비스 3개 active, 기존 timer 13개 복구. 기업 3개·추천1501·추천 성과·AI 설정 화면 모두 200.
- 환경 파일 hash와 모델 설정 불변: revision2, gpt-5.6-terra, overrides 없음. migration·새 AI 호출 없음.
- 운영 `verify_runtime.py`에서 artifact492/493/494의 정확한 hash와 보완 상태, 추천1501 연결, 미검토 SPY 분기를 확인했다. 수정 SELECT의 기간/계산 가능 지표 수는 로컬 대조와 같았다.
- 위 읽기 검증 전후 9개 테이블의 전체 row hash 불변: 추천1358, 점수요소32593, 포지션515, benchmark구성612, outcome1233, 재무period4038, 원천수치17575, normalized921480, 보고서468. 증거 `verification.json`.
- 운영 13309 Chrome: AAPL/NVDA/ARM 및 추천1501의 검토 상태 확인. AAPL 세부 열기, 390px 기업·추천 상세 넘침 없음. 최종 캡처 `production-aapl-desktop.png`, `production-aapl-review.png`, `production-aapl-mobile.png`, 검증 기록 `production-browser.json`. viewport 원복, 운영 AAPL 탭을 남겼다.

보조 PostgreSQL CI artifact 다운로드 한 건은 자동 승인 검토의 사용량 한도로 거절돼 다시 다운로드하지 않았다. 기존 로컬 SQL 실행과 GitHub 완료 결과, CI watch 로그로 검증을 기록했다. 이후 사용자의 계속 진행 요청 아래 PR 병합·운영 반영 도구는 정상 승인되어 완료됐다.
