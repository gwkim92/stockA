# 진행 중 인계

작업 브랜치 codex/purpose-fit-recovery-v1. 로컬 수정과 사전 검증 완료 후 CI·운영 반영을 진행 중이다. QA와 review에 변경/보호 경계를 기록했다.

현재 운영 성과 복구 대상은 2026-09-10 기준 1,009개, 66 batch×horizon이다. 기존 119개 성과를 보존하면서 최대 20 batch×horizon씩 실행하고, 잔여·기존 row·추천 점수/weight·포지션 불변성을 재조회한다. 기업 실제 AI 생성 표본 NVDA/AAPL/ARM은 아직 실행하지 않았다. 기존 모델 gpt-5.6-terra/revision 2를 유지한다.

로컬 읽기 전용 preview 18779 → 웹 13321, 테스트 PostgreSQL 55487은 본 작업의 임시 프로세스다. 최종 화면은 사용자 터널 13309에서 확인한다. 기존 사용자 문서 변경은 별도로 보존한다.
