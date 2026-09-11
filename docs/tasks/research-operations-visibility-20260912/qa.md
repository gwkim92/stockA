# 검증

- AWS 개인 계정/인스턴스/보안그룹 연결 확인. Chrome의 변경 미리보기에서 SSH 단일 /32 규칙만 변경. 저장 성공 및 10개 규칙 수 보존.
- 실제 SSH, 웹 HTTP200, Chrome /data-health 렌더 확인. LaunchAgent SIGTERM 후 PID 교체와 HTTP200 자동 복구 확인. evidence/access.json.
- 임시 Postgres 통합/관련 Python 검사 169개 통과. 반복 상태 조회는 pending claim을 닫거나 AI를 호출하지 않으며 새로운 원천으로 바뀐 pending claim 식별자를 유지.
- 기존 live adapter107개 및 venv FastAPI18개 통과. 시스템 Python의 fastapi 미설치 오류는 프로젝트 venv로 해당18개를 실행해 해소.
- UI 단위2개 통과. Next.js 빌드·타입 통과. Chromium desktop/mobile4개 시나리오 통과(대기/불명 결과/예산 소진/검색/필터/미조회/빈목록). 최초 selector 오류는 실제 접근성 role/name으로 수정. 모바일 패널 여백 보완 후 빌드·타입·4개 브라우저 시나리오 재통과.
- 배포/운영 새 화면은 아직 미검증. 기존 decision-daily 복구 실행은 결과 확인 중.
