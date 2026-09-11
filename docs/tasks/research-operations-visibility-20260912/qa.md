# 검증

- AWS 개인 계정/인스턴스/보안그룹 연결 확인. Chrome의 변경 미리보기에서 SSH 단일 /32 규칙만 변경. 저장 성공 및 10개 규칙 수 보존.
- 실제 SSH, 웹 HTTP200, Chrome /data-health 렌더 확인. LaunchAgent SIGTERM 후 PID 교체와 HTTP200 자동 복구 확인. evidence/access.json.
- 임시 Postgres 통합/관련 Python 검사 169개 통과. 반복 상태 조회는 pending claim을 닫거나 AI를 호출하지 않으며 새로운 원천으로 바뀐 pending claim 식별자를 유지.
- 기존 live adapter107개 및 venv FastAPI18개 통과. 시스템 Python의 fastapi 미설치 오류는 프로젝트 venv로 해당18개를 실행해 해소.
- UI 단위2개 통과. Next.js 빌드·타입 통과. Chromium desktop/mobile4개 시나리오 통과(대기/불명 결과/예산 소진/검색/필터/미조회/빈목록). 최초 selector 오류는 실제 접근성 role/name으로 수정. 모바일 패널 여백 보완 후 빌드·타입·4개 브라우저 시나리오 재통과.
- 배포/운영 새 화면은 아직 미검증. 기존 decision-daily 복구 실행은 결과 확인 중.

- 운영 decision-daily 복구: 23개 단계 completed, failed_step_count=0, systemd Result=success/ExecMainStatus=0. stale/failed/missing job0개. 기존 실행 증거 gate와 추천 outcome 실행 gate가 제거됐고 새 원천 부족 항목을 포함한7개 주의는 유지. evidence/recovery.json.

## 운영 검증 완료

PR66 CI 5개 통과 후 `ba63c79cdbb1fcc75a67673975f315dbce8948cf` 배포. Linux artifact web tree 일치, SHA/lock/BUILD_ID 확인. EC2에서 Next 빌드를 실행하지 않았다. 상세 결과는 evidence/activation.json, verification.json.

- API queue와 기존 worker 계획 동일. 반복 GET 전후 claim 2개, AI invocation 41087개 보존; 모델 SQLite 불변.
- 33개 대상: current 2(A/ADBE), due 13, waiting_for_source 18. 일일 사용 2/5. EROK는 이 시점 due, AAPL은 waiting_for_source이므로 과거 상태를 재사용하지 않았다.
- 복구 decision-daily 23/23 성공, stale/failed job 0.
- 웹 3000/13000 HTTP200, 14개 timer, 13개 보호된 batch profile, attention 0.
- 최초 배포 직후 status artifact에 타이머 중지 시점이 잠시 남아 guard assertion이 실패했다. 실제 systemd와 다음 1분 자동 갱신의 protected 상태를 확인한 뒤 read-only 검증을 재실행해 통과했다.
- 실제 Chromium desktop 1440px/mobile 390px: 검색·상태 필터, HTTP200, 가로 overflow 없음. production-*.png와 production-ui.json은 실제 서비스 캡처이며 기존 research-refresh-*.png는 합성 fixture다.
- 브라우저 점검의 최초 기대값은 과거 EROK 원천 대기를 가정해 실패했다. 운영 API의 현재 EROK due/AAPL waiting_for_source를 확인하고 AAPL로 원천 필터를 검증했다. 이는 제품 수정이 아니라 검증 입력 보정이다.
