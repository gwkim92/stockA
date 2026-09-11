# 검증 기록

- macOS 실제 subprocess: 조용한 정상 작업, 16MiB(시험에서는 1KiB) 출력 상한, spawn 실패, timeout 시 SIGTERM 무시 후손 정리, 부모 SIGTERM 시 중단 기록 및 자식 정리 통과.
- 최초 SIGTERM 실험에서 InterruptedError가 selectors에 의해 재시도되는 문제를 재현해 전용 예외로 교정했다. 수정 후 실제 signal/후손 검사가 통과했다.
- 단계 진행 파일의 정상/기한 초과/이전 부팅/이전 실행/중단/손상 판정과 비밀 필드 제거, 감시 기록 3분 경과 시 stale 표시 통과.
- artifact/orchestrator/scheduler focused 검사 및 CLI/live adapter 214개 회귀 통과. 추가 guard 포함 CLI/API 묶음 227개 통과.
- scheduler invocation 및 orchestrator verification script 통과. 기존 스크립트의 오래된 profile 8개 기대값과 뉴스가 full-recovery의 첫 단계라는 가정은 현재 15개 구성 및 수집→보강→AI 의존 순서에 맞췄다.
- 워크플로 YAML와 Python 문법 및 git diff 검사 통과. Linux CI와 운영 systemd/cgroup 시험은 배포 전후 기록을 추가한다.
