# 인계

- branch: fiture/runtime-resource-guard, base develop fd8226630f3a9f26cdc7898e2e700239eac94f1d (PR #62 merged). 앞선 자동화 코드는 아직 서버에 활성화하지 않았다.
- 개인 AWS recovery Chrome tab 1527793616은 로그인 화면이다. 사용자에게 계정 115623963546 로그인을 요청했다. 기존 IAM 탭 1527793408에도 로그아웃 overlay가 있다. AWS write 또는 재부팅은 이번 턴에 수행하지 않았다.
- 원인 증거: docs/tasks/ai-model-settings-v1/handoff.md의 Recovery and deployment evidence에 9월 10일 동일 Next 서버 빌드 무응답/재부팅 복구가 있다. 당시 OOM 로그가 없었고 이번에도 커널 로그를 읽지 못했으므로 메모리 고갈로 확정하지 않는다. 별도 수집 payload 확대 문제는 docs/tasks/tossinvest-shadow-daily-resource-guard-v1/handoff.md에 기록돼 있다.
- 표준 npm build를 보호하고 기존 CI runtime artifact의 자동 trigger와 source/integrity manifest를 추가했다. 이전 research-automation activate.py도 해당 CI manifest를 사용할 수 있다.
- 복구 후 inspect_host.py를 기존 venv Python으로 실행하여 bounded read-only 증거를 얻는다. 이전 remote /tmp/stocka-research-activate.py는 무제한 build 버전일 수 있으므로 절대 재실행하지 말고 새 파일을 업로드한다.
- 우선순위는 서버 복구 → 실제 자원/동시 작업/로그 확인 → CI 결과물 배포 → research-maintenance 두 차례 실행/보호 데이터 검증/원래 타이머 복원/웹 확인이다. 로그인 없이 회사 AWS 계정이나 로컬 AWS CLI write로 대체하지 않는다.
