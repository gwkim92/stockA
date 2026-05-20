# Local Runtime Status Orchestrator

생성일: 2026-05-20

## 목적

`stockanalysis-operations local-runtime-status`는 local-first runtime의 현재 상태를 한 번에 확인하는 read-only command다.

이 명령은 서비스를 시작하거나 scheduler를 설치하지 않는다. 단지 다음을 점검한다.

- runtime root 존재 여부
- repo-outside env file 존재 여부
- DB boundary 설정 여부
- artifact root 설정 여부
- FastAPI local live endpoint 응답 여부
- Next.js local cockpit 응답 여부
- 다음 수동 실행 명령

## 왜 LaunchAgents를 계속 금지하는가

Mac `launchctl`/LaunchAgents는 단순한 테스트 명령이 아니라 host-level persistent mutation이다.

- 한 번 설치하면 Codex 세션이 끝나도 계속 반복 실행될 수 있다.
- env 파일과 API key를 가진 command가 무인 실행된다.
- 잘못된 interval/command면 API quota를 소모하거나 DB에 잘못된 데이터를 반복 적재할 수 있다.
- 중지/rollback 명령까지 검증하지 않으면 사용자가 원인을 찾기 어렵다.
- 현재 local-first 단계에서는 수동 worker 실행과 상태 확인만으로 충분하다.

따라서 이 프로젝트에서는 `launchctl` 실제 실행과 LaunchAgents write/delete를 명시 승인 전까지 금지한다.

## 현재 사용법

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli local-runtime-status --skip-http-probes
```

로컬 서버가 떠 있을 때는 probe를 켠다.

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli local-runtime-status
```

출력은 JSON이며, env 값은 출력하지 않는다. env key 이름과 설정 여부만 표시한다.

Codex sandbox가 local HTTP probe를 막는 경우 endpoint status는 `probe_blocked`가 된다. 이 상태는 서비스 down을 의미하지 않는다. 호스트 셸에서 같은 명령을 다시 실행하면 실제 연결 여부를 확인할 수 있다.

## 다음 단계

이 status command 다음에는 다음을 붙인다.

- local one-command smoke runner
- 수동 market/news/AI ingest smoke. Implemented in `manual-local-ingest-smoke`.
- `/data-health`가 local runtime status artifact를 읽는 경계
- 선택 사항: 로컬 반복 실행 preview
