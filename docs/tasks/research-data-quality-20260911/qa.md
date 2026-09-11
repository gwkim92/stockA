# 검증 기록

## 로컬 코드·실데이터

- Python 관련 6개 모듈 160테스트 통과: content review, live adapter, purpose fit recovery, equity reporting, cutoff, equity contract v3.
- Frontend 전체 44파일 / 532테스트 통과. 마지막 접기 UI 수정 후 해당 컴포넌트 3테스트 재통과.
- Next.js typecheck 및 격리 production build 통과. 마지막 UI 수정 후 build 재통과.
- 임시 PostgreSQL 17에서 기존 시간대/cutoff 회귀와 새 4개 SQL 시나리오 통과: 주식 수 날짜 제외, 실제 최신 기간의 결측 유지, 미래/미상 보고일 제외, 비교군 미검증 표시. 전용 DB의 transaction 안에서 fixture를 만들고 rollback했다. 전용 클러스터는 종료했다.
- 수정된 실제 SELECT를 운영 DB에서 read-only로 실행: NVDA 2026-01-25, AAPL 2025-09-27, ARM 2025-03-31. 결과는 `corrected-contexts.json`에 보관.
- 공식 SEC companyfacts NVDA/AAPL/ARM 모두 조회 성공. 새 AI 호출·운영 DB 쓰기 없음.

## 실제 Chrome

로컬 preview는 운영 API를 GET으로 읽고 실제 새 review adapter를 적용했다. 18790 API/13330 Next.js는 이번 작업 전용이며 운영 13309와 구분한다.

- AAPL desktop: 보완 상태가 기본 펼침, 세부 3항목은 접어서 표시. 실제 클릭으로 세부 펼침과 공식 Apple FY2025 원문 새 탭 이동 확인.
- AAPL/NVDA/ARM 390px: 각 기업의 맞는 검토 요약 표시. scrollWidth=clientWidth=390.
- 추천1501: 같은 AAPL 검토 결과 노출, 390px 넘침 없음, 브라우저 error 로그 0.
- 원 보고서 본문은 유지되고 검토가 전체 사실 인증/사람의 투자 승인이 아님을 표시한다. 미등록 보고서는 계속 미검토다.
- 캡처: `output/research-data-quality-20260911/aapl-desktop.png`, `aapl-mobile.png`, `arm-mobile.png`, `recommendation-desktop.png`. `local-browser.json`에 일부 DOM 검증 기록.

기존 Playwright 세션의 캡처는 시간 초과됐다. CUA의 새 Chrome 탭에서 최종 캡처를 확보했다. 첫 temp build의 node_modules symlink는 Turbopack root 제한에 걸렸으나 격리 경로에 로컬 dependency를 복사한 뒤 통과했다. 제품 의존성이나 설정은 변경하지 않았다.

## 운영 반영

로컬 검사 완료. CI, 배포와 실제 운영 UI 결과는 수행 후 이 절에 추가한다. 로컬 preview가 운영 반영을 증명하지 않는다.
