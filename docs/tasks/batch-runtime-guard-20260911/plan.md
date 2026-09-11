# 실행 순서

1. 증거/정책: systemd/cgroup 및 DB 제한 확인, 8GiB 호스트용 합산/개별 예산 결정.
2. 구현: artifact timeout 프로세스 그룹 정리, 진행 파일과 상태 판정, systemd 생성기 제한과 기존 상태 보고서 연계.
3. 검증: 실제 subprocess 후손/신호/시간 초과, 정상 침묵/기한 초과/프로세스 중단/손상 파일 판정, 기존 orchestrator/scheduler/API 회귀.
4. 운영: 현재 설정 백업, CI 통과 develop 배포, 기존 unit drop-in과 shared slice 적용, 제한된 별도 service 실패 실험 후 실제 재무 수집 확인.
5. 인계: 배포 SHA, 실제 cgroup 값, API/서비스/데이터 보존 근거, 남은 장기 부하·재개 범위 기록.
