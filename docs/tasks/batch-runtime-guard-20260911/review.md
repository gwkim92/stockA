# 검토 기록

검토 범위: 하위 프로세스 생명주기, 합산/개별 자원 정책, 진행 기록·API 경계, 적용/복원 경계.

- SIGTERM은 예외로 제어 루프를 빠져나오며 원래 signal handler를 복원한다. timeout/cancel/output-limit에서 POSIX process group을 정리하고 systemd control-group 종료가 별도 session 후손을 보완한다.
- stdout/stderr를 순차로 파일에 기록하고 각 16MiB에서 중단하므로 메모리·디스크에 무제한 쌓지 않는다. 성공/실패/timeout/중단/출력 초과는 서로 다른 상태다.
- 진행 파일에는 실행 ID·단계·시각·완료 단계 개수만 남기며 오류 본문·환경 값을 넣지 않는다. 상태 보고서는 명시된 step 시간 초과만 판정하고 무출력만으로 중단시키지 않는다.
- batch slice 2GiB/CPU 100%, 개별 1GiB, DB 별도 3GiB는 8GiB 호스트에서 OS/API/웹 여유를 남긴다. DB client 종료를 DB transaction 완료/rollback의 증거로 취급하지 않으며 불명확한 결과를 자동 재실행하지 않는다.
- 배포는 정확한 develop을 검증하고 env/모델 hash·웹 build를 보존한다. unit 원본과 DB limit을 서버의 private task directory에 백업한다. 배포 중 active batch가 있으면 중단시키지 않고 적용을 중지하며 기존 timer를 복원한다.
- Docker limit은 해당 컨테이너 재시작에는 보존되지만 컨테이너 재생성 명령에는 다시 포함해야 한다. 이 작업은 생성 권한/IAM/주문 자동화나 일반적인 실패 작업 재개를 추가하지 않는다.
- 별도 에이전트 검토는 사용하지 않았다. 운영 인수 기준은 실제 cgroup 제어와 정상 수집·웹/DB 응답 확인이다.
