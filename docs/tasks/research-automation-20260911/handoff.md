# 인계

브랜치: fiture/research-automation. 자동화 기능과 로컬/운영 읽기 검증을 구현했다. 배포와 실제 반복 실행 증거는 후속으로 추가한다.

- 신규 CLI: `research-maintenance-run --env-file <ENV> --artifact-root <RUNTIME>/research-automation-artifacts [--execute]`. 날짜 기본값은 UTC 오늘이다.
- 신규 systemd profile: `research-maintenance`, 매일 America/New_York 00:20/06:20/12:20/18:20, 1회 최대 3기업.
- 부모 pipeline: research_maintenance. 기업별 원자적 갱신 receipt: research_statement_refresh.
- DB 내부 변경 전 백업: 기업별 ops.pipeline_run.config_json.backup_before. 공개 응답·안전한 최근 상태: artifact root/research-maintenance.
- 신규 API 보조 필드: `/api/data-health.research_maintenance`. 실제 큐 개수는 최근 완료 시점의 값이다. 기존 pipeline_runs에도 새 job이 포함된다.
- 다음 계획과 수작업 구분: automation-inventory.md.
- 미관련 dirty 문서와 이전 pilot 파일은 수정/재실행하지 않았다.
