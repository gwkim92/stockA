평가 이력 API가 있어도 화면에서 기록 당시 판단과 현재 자료를 비교할 수 없었던 경로를 완성합니다. 평가 목록·상세 페이지를 연결하고, 별도 읽기 전용 비교 API에서 저장 해시와 복사 필드의 일치 여부, 추천/thesis 변경, 평가 기준일 이후 동일 관찰 기간의 측정 성과를 표시합니다. 기존 frozen-history API는 현재 원천 조회와 분리됩니다.

- bigint/keyset, 누락·legacy·손상·현재 원천 오류, 0/null 구분. 스키마·추천 점수·가중치·benchmark·주문 변경 없음.
- Python/HTTP 72, 분석 93, CLI 107, 실제 disposable PostgreSQL 10개 통과. 기존 migration 35개를 테스트 DB에만 적용.
- 웹 단위 517개, build/typecheck, 기존 보유·성과 브라우저 36개, 신규 17상태×3화면 51개 검증 통과. 새 검증을 CI에 연결.
- 완료된 원격 기능 브랜치 49개의 삭제 전 SHA와 복구 근거를 기록. main/develop 유지.

실서버 배포·실데이터 갱신은 포함하지 않습니다. 자세한 인계: docs/tasks/evaluation-history-completion-v1/handoff.md.
