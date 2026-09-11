# 인계

현재 브랜치: `fiture/research-source-refresh`. 로컬 구현·DB·API·화면 회귀 통과. CI/배포/실제 모델 canary는 아직 대기다.

새 실행 경로: `stockanalysis-operations research-report-refresh-run --env-file <ENV> [--symbol AAPL] --execute`. 실행 일자는 UTC 오늘이며, 종목 필터는 공통 한도를 우회하지 않는다. 기존 `research-maintenance` 뒤와 기존 daily reporting이 같은 실행기를 사용한다.

운영 대상은 개인 계정 `115623963546`, `i-029d51b163fb07b61`, `3.211.40.142`, t3.large이다. 2026-09-11 Chrome 콘솔에서 다시 확인했다. 로컬 SSH는 현재 IP allowlist 차이로 접근되지 않아 로그인된 EC2 Instance Connect를 사용한다. 보안그룹은 변경하지 않는다.

순서: 정확한 develop과 Linux CI 산출물 확인 → `/opt/stockanalysis/runtime/research-source-refresh-20260911`에 artifact 배치 → `apply_server.py <develop sha>` → 제한된 `verify_server.py --execute` → 14개 기존 timers 및 13개 batch 보호 상태·3개 서비스 확인. EC2에서 Next.js 빌드는 실행하지 않는다.

중단 시 `started.json`/`canary-started.json`을 확인한다. 배포나 모델 호출을 그대로 재실행하지 않는다. 저장 receipt를 먼저 대조하고, canary가 프로세스 강제 종료로 끊긴 경우 체크포인트의 기존 timers를 복원한다. 모델 성공을 주장하려면 실제 primary receipt와 company API 버전 일치가 필요하다.
