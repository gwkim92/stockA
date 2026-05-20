# Server Scheduler Invocation Boundary

생성일: 2026-05-20

## 목적

로컬 ingest worker를 나중에 서버 측 scheduler에서 호출할 수 있도록 command/manifest preview를 만든다.

## 핵심 경계

- 이 문서는 scheduler 배포가 아니다.
- 실제 cron/systemd/Kubernetes/managed scheduler 등록은 하지 않는다.
- Mac LaunchAgents/`launchctl` 실행은 하지 않는다.
- `.env` 값, DB URL, API key, bearer token은 report에 나오면 안 된다.

## 호출 대상

최종 scheduler가 호출해야 하는 backend 경계는 다음이다.

```bash
PYTHONPATH=<repo>/src python -m stockanalysis.operations.cli local-ingest-worker-run ...
```

worker는 market/news/AI evidence job을 실행하고, repo-outside worker report와 latest manual smoke report를 갱신한다.
