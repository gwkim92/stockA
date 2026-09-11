# 진행 인계

브랜치 fiture/batch-runtime-guard, 기준 develop 502eb679. 이전 서버 복구 기록과 배포/검증 script 교정도 보존한다. 다른 task의 dirty 문서는 변경/커밋 대상에서 제외한다.

구현: operations/batch_runtime.py의 합산/개별 정책·진행 기록·읽기 감시, artifact_runner의 프로세스 그룹 정리와 출력 상한, CLI/orchestrator 단계 기록, scheduler-status 및 data-health API 관측 필드. 기존 status timer를 15분에서 1분으로 바꾸는 적용 script는 apply_server.py다.

로컬 검증은 qa.md. 다음은 Linux CI 확인 후 develop 병합 → apply_server.py에 정확한 merge SHA 전달 → 제한된 별도 systemd timeout/OOM 실험 → research-maintenance 실제 실행과 보호 데이터/웹/API 검증이다. 서버 안에서 빌드하지 않는다. 배포 checkpoint가 생기면 같은 script를 무조건 반복하지 않는다.
