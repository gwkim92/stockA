# 뉴스 식별자 충돌 수정 및 운영 격리 완료

2026-09-11 KST. PR #54를 develop에 통합하고 EC2에 배포한 뒤 source-document-22/event-19를 격리했다. 실제 AAPL 분석 입력과 운영 Chrome에서 효과를 확인했다.

## 원인과 구현

Yahoo RSS의 `?src=A00220&yptr=yahoo`가 article GUID로 처리돼 여러 기사가 같은 문서/이벤트를 덮어썼다. 같은 hash는 5월 fixture에도 있다. 변경 전 실제 화면에는 시장 뉴스 한국어 제목, Google Cloud 발췌, AeroVironment 영문 제목이 함께 표시됐다.

잘못된 GUID만 기사 URL로 식별하고 정상 publisher ID를 유지한다. 격리 문서는 RSS 재수집으로 덮어쓰지 않는다. 별도 격리 service가 사전 지문을 잠금 안에서 대조하고 전체 변경 전 문서/이벤트/연결을 ops.pipeline_run에 보존한다. 금융 이력과 AI 산출물, 원문/번역/발췌는 삭제하지 않는다. 원천 상세·빠른 패널·기업 검토 원천에서 불일치를 알리고 혼합 번역과 발췌를 표시하지 않는다.

## 운영 증거

- PR #54: https://github.com/gwkim92/stockA/pull/54
- 구현 030ea38c1eece6941a6803ffc865f8126b4e8b56, develop/EC2 9c7ff0d6ca8874e3155915e3d8d9b63594d48d3e.
- Linux artifact run 34549050262, BUILD_ID wi_q7XkMmw6zRhFnen2a7, SHA-256 f66d9df185672d6b795e4ccf56b158bfbc2c61e7ca6077103eb2cda80fdda138.
- 개인 AWS 115623963546 / i-029d51b163fb07b61 / us-east-1을 IMDS로 재확인했다. 서비스 3개 active, 주요 route 200, API ready=ok, 타이머 13개 복원.
- 모델은 gpt-5.6-terra, revision 2, overrides 없음. 모델 설정과 환경 파일 hash/권한 보존. migration 없음.
- 격리 run 23821: 문서 22, 이벤트 19, 종목 연결 1개, 테마 연결 6개. DB archive가 사전 snapshot과 완전히 같음을 확인했다.
- 기존 행 지문 보존: 추천 1,358, 점수 32,593, 포지션 515, benchmark 612, 추천 성과 1,233, thesis 성과 746, 기업 AI 보고서 468. 문서 22의 청크 1개, extraction artifact 245개 보존.
- AI 추가 호출 0. 추천 weight, 평가 기준, 금융 기록, 실거래 경계 변경 없음.
- 현재 AAPL research context를 읽어 event 19/document 22 부재를 확인했다. 원천 API는 integrity_status=quarantined_identity_conflict, korean_title/summary=null, excerpts=[]를 반환한다.

## 검증

관련 Python 212개, 실제 임시 PostgreSQL 4개, 웹 524개, Next typecheck/build 통과. PR #54의 분석 계약 Python 3.11/3.13, Postgres atomic/cutoff, 평가 이력, 전체 웹 품질 CI 모두 통과했다. 전체 웹 CI run 34549052975는 11분 38초에 성공했다.

Chrome 사용자 터널 http://127.0.0.1:13309에서 원천 상세와 AAPL 검토 노트 × desktop/mobile 4화면 모두 200, 불일치 경고, 혼합 번역 부재, 가로 넘침 없음, pageerror 없음을 확인했다. 배포 중 이전 페이지의 data-health 사전 로딩 요청 1개가 connection reset으로 기록됐으나 해당 검증 화면은 정상 응답했다.

캡처 output/playwright/news-integrity-*.png, 실행/지문/API/화면 검사 output/news-source-consistency-20260911/. 운영 보존 경로 /opt/stockanalysis/runtime/news-source-consistency-20260911/. activation.json, repair-started.json, repair-receipt.json, repair-verified.json이 있으므로 재실행하지 않는다. rollback용 이전 소스와 Next build도 이 경로에 있다. 임시 PostgreSQL 55488은 종료했다.

## 한계와 다음 작업

여러 달 덮어쓴 원문 역사를 완전히 복구한 것은 아니다. 기존 AAPL artifact 493 및 과거 추천은 그대로 보존되며 내용 검토가 필요하다. 실제 AI 보고서를 재생성하거나 검토 통과 처리하지 않았다. 정상 ID를 가진 같은 기사의 수정에 대해 모든 파생 데이터를 버전 관리하는 기능은 별도 과제다. 수정된 parser의 다음 정규 RSS 수집 실행은 아직 관찰하지 않았다.

다음 독립 작업은 전체 추천 성과 탐색이다. 현재 /performance는 지정 종료일의 attribution_run과 보유 스냅샷을 요구하므로 전체 추천 outcome backfill을 모두 표시하지 않는다. 기존 귀속 보고서 의미를 보존하면서 종목/추천일/관찰 기간/실제 측정 종료일/benchmark를 비교하고 당시 추천과 thesis로 돌아가는 조회를 추가한다. 서로 다른 관찰 기간을 하나의 수익률로 합치지 않는다.

화면 최종 검수에서 격리 자료에 대한 '저장된 요약 없음' 문구가 오해를 줄 수 있어 '표시할 요약 없음'으로 보정하고 원천 유형을 한국어로 표시하는 작은 후속 변경을 준비했다. 후속 배포 증거는 아래에 추가한다.
