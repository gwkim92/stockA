# 실행 순서

1. 증거/정책: systemd/cgroup 및 DB 제한 확인, 8GiB 호스트용 합산/개별 예산 결정.
2. 구현: artifact timeout 프로세스 그룹 정리, 진행 파일과 상태 판정, systemd 생성기 제한과 기존 상태 보고서 연계.
3. 검증: 실제 subprocess 후손/신호/시간 초과, 정상 침묵/기한 초과/프로세스 중단/손상 파일 판정, 기존 orchestrator/scheduler/API 회귀.
4. 운영: 현재 설정 백업, CI 통과 develop 배포, 기존 unit drop-in과 shared slice 적용, 제한된 별도 service 실패 실험 후 실제 재무 수집 확인.
5. 인계: 배포 SHA, 실제 cgroup 값, API/서비스/데이터 보존 근거, 남은 장기 부하·재개 범위 기록.

## 완료 후 다음 구현

1. 원천 버전 전파: `operations/research_maintenance.py`가 수집 실행의 config_json에 저장하는 source_sha256와 `ai/equity_research_batch.py`의 request_hash·`ai/equity_research_persistence.py`의 완료 receipt를 연결한다. 자료를 성공적으로 교체한 경우에만 해당 기업의 분석/리포트를 재생성 후보로 만든다. 같은 입력이면 중복 호출하지 않고, 생성 중 원천이 바뀌면 최신 자료와 일치하지 않는 결과임을 표시한다. 기존 JSON metadata를 우선 검토하며 schema 변경은 별도 결정 전까지 하지 않는다.
2. 중단 후 재개: 이번 단계 진행 기록만으로 DB 작업을 재실행하지 않는다. 기존 invocation/result fingerprint와 완료 receipt를 먼저 대조하고, 결과가 확인된 단계는 건너뛰며 불확실한 DB 변경은 reconcile 상태로 둔다.
3. 디스크 자동 관리: raw evidence·실행 로그·before-image의 참조 관계와 보존 기준을 정한 뒤, 아직 참조되는 원천과 복구용 백업을 보존하는 정리 작업을 추가한다. 삭제 전 preview와 사용량 기준을 검증한다.

이번 배포에서는 위 후속 변경을 구현하거나 추천 weight/주문 경계를 바꾸지 않았다.
