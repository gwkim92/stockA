# 검증 기록

- macOS 실제 subprocess: 조용한 정상 작업, 16MiB(시험에서는 1KiB) 출력 상한, spawn 실패, timeout 시 SIGTERM 무시 후손 정리, 부모 SIGTERM 시 중단 기록 및 자식 정리 통과.
- 최초 SIGTERM 실험에서 InterruptedError가 selectors에 의해 재시도되는 문제를 재현해 전용 예외로 교정했다. 수정 후 실제 signal/후손 검사가 통과했다.
- 단계 진행 파일의 정상/기한 초과/이전 부팅/이전 실행/중단/손상 판정과 비밀 필드 제거, 감시 기록 3분 경과 시 stale 표시 통과.
- artifact/orchestrator/scheduler focused 검사 및 CLI/live adapter 214개 회귀 통과. 추가 guard 포함 CLI/API 묶음 227개 통과.
- scheduler invocation 및 orchestrator verification script 통과. 기존 스크립트의 오래된 profile 8개 기대값과 뉴스가 full-recovery의 첫 단계라는 가정은 현재 15개 구성 및 수집→보강→AI 의존 순서에 맞췄다.
- 워크플로 YAML와 Python 문법 및 git diff 검사 통과.
- Linux CI: runtime 코드 최종00b5cd38의 Batch Runtime Guard(34584499644), Evaluation History(34584499636), Financial Period Integrity(34584499557), Web Product Quality(34584499558) 모두 통과. 이후13ae4751은 운영 검증 script만 추가했으며 batch(34601399165), history(34601399175), financial(34601399174), web(34601399146) 모두 재통과했다. 웹 CI는 실제 Chromium의 기업 노트/평가 이력/투자자/보유·성과/thesis·원천/기업·근거/뉴스·테마 시나리오와 빌드·타입·단위 검사를 통과했다.
- 운영 develop3692adcd 배포, env/모델 hash 및 기존 웹 build 불변. shared slice 실제 kernel memory.max2147483648, memory.high1610612736, memory.swap.max0, cpu.max100000/100000, pids.max512.
- 64MiB 별도 systemd 시험: 시간 초과 Result=timeout/exit15, 메모리 초과 Result=oom-kill/exit9, 두 control group 모두 종료 후 비어 있음. 각 시험 직후 웹/API3경로 200.
- 실제 연구 수집2회, parent23905/23909 및 child6개 succeeded, 6개 서로 다른 기업 fresh, before-image 존재, 보호 데이터 hash 불변. 결과 대기열 due14/fresh18/retry_wait0/reconcile0.
- 기존 timer14개 복구. 운영 API batch_runtime=protected, shared/database limits=true,13/13,attention0, 관측2초 전. research succeeded/completed_steps1. overall data-health attention_required는 기존 이슈로 유지.
- 수동 검증 완료 후 별도 start 없이 status report가13:04:14UTC로 갱신됐고 protected13/13·attention0을 유지했다. 분 단위 자동 감시 실행도 확인했다.
- 로컬 SSH는 변경된 공인IP 미허용으로 timeout. AWS 상태검사3/3 및 개인 계정 브라우저SSH 성공으로 서버 장애와 구분했다. 보안그룹/재부팅 변경 없음. 서버 내부 HTTP 검증 완료; 현재 PC13309 터널의 브라우저 검증은 연결 경계로 미완료.
