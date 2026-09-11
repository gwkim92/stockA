# 진행 인계

브랜치 fiture/batch-runtime-guard, 기준 develop 502eb679. 이전 서버 복구 기록과 배포/검증 script 교정도 보존한다. 다른 task의 dirty 문서는 변경/커밋 대상에서 제외한다.

구현: operations/batch_runtime.py의 합산/개별 정책·진행 기록·읽기 감시, artifact_runner의 프로세스 그룹 정리와 출력 상한, CLI/orchestrator 단계 기록, scheduler-status 및 data-health API 관측 필드. 기존 status timer를 15분에서 1분으로 바꾸는 적용 script는 apply_server.py다.

PR #64가 develop `3692adcda9203e67d967a4873775e2711ba0d172`로 병합됐고 2026-09-11 13:01 UTC 운영 배포 완료. 웹은 기존 build `WcwTXPpZJZtUkdFHyJ8-t`를 유지했으며 서버 빌드는 실행하지 않았다. env 3개와 AI 설정 hash를 보존했다.

실제 cgroup: batch 합산 MemoryMax 2GiB, MemoryHigh 1.5GiB, CPUQuota 100%, swap 0, TasksMax 512. 기존 활성 data profile 13개에 개별 1GiB/전체 시간 상한을 적용했다. Docker PostgreSQL은 3GiB/no-extra-swap이며 재시작에 유지된다. 재생성 명령에는 같은 flags가 필요하고 누락은 status monitor가 감지한다. 기존 status timer를 1분 주기로 변경했다. 14개 timer(13 data + 1 status)가 복원됐다. 기존 비활성 KR 2개는 그대로다.

64MiB의 별도 시험 unit에서 timeout과 oom-kill을 각각 확인했고 cgroup이 비워졌다. 두 실패 직후 API8787·web3000·public web13000의 내부 HTTP 검사 모두 200. 정상 research-maintenance 두 번도 성공: parent23905/23909, child23906/23907/23908/23910/23911/23912, BMNR/COST/DG/DIS/ELF/EROK 6개 중복 없이 fresh. 추천/score/보유/benchmark/outcome/AI artifact 및 대상 밖 재무 hash 불변, 같은 DB before-image 확인. API batch_runtime protected13/13, attention0, research succeeded/completed_steps1. 실제 증거는 evidence/live-verification.json, 원본은 서버 `/opt/stockanalysis/runtime/batch-guard-20260911`.

접속 이슈: 배포 전 로컬 SSH TCP timeout은 현재 PC IP14.32.108.104가 기존 allowlist에 없는 상태였다. AWS 개인 계정/고정 IP/상태 검사3/3과 브라우저 SSH에서 uptime·가용메모리6898MiB를 확인했다. 서버 재시작과 보안그룹 변경 없이 Chrome EC2 Instance Connect로 배포/검증했다. 로컬13309 터널은 현재 연결되지 않음. 사용자 PC에서 해당 웹을 보려면 승인된 접속망 또는 별도 승인된 단일IP SSH 규칙 갱신이 필요하다.

완료 범위는 이번 배치 보호와 짧은 실패/정상 실행 검증이다. 과거 장애를 OOM으로 확정하지 않는다. 인위적 canary oom-kill은 과거 사고 원인의 증거가 아니다. 장기간 최대 부하 안정성은 아직 검증하지 않았다. DB client 종료만으로 transaction rollback을 보장하거나 불확실한 실행을 자동 재전송하지 않는다. overall data-health는 기존 attention_required 상태이며 별도의 원천/성과 이슈는 이 작업으로 닫지 않았다. EROK의 이번 7 facts 수집 성공도 전문 분석 차단 해제의 증거는 아니다.

다음 순서: 원천 자료 버전 변경을 분석/리포트의 재생성 대상으로 전파 → 단계별 재개와 실행 결과 대조 → raw/backup 보존 기간과 디스크 상한 자동화. 추천 weight/실거래는 계속 범위 밖. 현재 적용/시험 checkpoint가 있으므로 apply_server.py나 verify_server.py를 무조건 반복하지 않는다. 부분 복원은 started.json과 unit-backup.json의 실제 이전값을 대조한다.
