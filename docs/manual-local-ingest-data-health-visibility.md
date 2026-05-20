# Manual Local Ingest Data Health Visibility

생성일: 2026-05-20

## 목적

이 작업은 `stockanalysis-operations manual-local-ingest-smoke`의 최근 summary report를 `/api/data-health`와 `/data-health`에서 확인하게 만든다.

핵심 구분은 다음이다.

- `preview_not_executed`: 실제 provider 호출과 DB write 없이 실행 계획만 검토했다.
- `passed`: `--execute`로 market/news/AI jobs를 artifact runner가 실행했고 실패가 없었다.
- `failed`: 하나 이상의 artifact run이 실패했다.
- `not_configured` 또는 `missing_report`: FastAPI runtime이 summary report를 아직 읽지 못한다.

## Runtime 연결

summary report는 repo 밖에 둔다.

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke \
  --output /private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json
```

FastAPI env에는 값 자체가 아니라 파일 경로만 연결한다.

```bash
STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT=/private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json
```

## 보안 경계

- API/화면은 DB URL, API key, bearer token, repo-inside `.env` 값을 노출하지 않는다.
- `data_operations_env_file`, `python_executable`, raw command argv는 data-health DTO에 싣지 않는다.
- 실제 `--execute`는 provider quota와 DB write를 유발할 수 있으므로 자동으로 실행하지 않는다.
- Mac LaunchAgents/`launchctl` 실제 설치는 여전히 금지다.

## 화면 의미

`/data-health`의 “수동 단발 실행 증거” 카드는 자동 반복 실행 상태가 아니다. 사람이 단발 수집 smoke를 실행했거나 실행 계획을 만들었는지 확인하는 운영 증거다.
