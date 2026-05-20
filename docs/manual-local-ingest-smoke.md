# Manual Local Ingest Smoke

생성일: 2026-05-20

## 목적

`stockanalysis-operations manual-local-ingest-smoke`는 local-first runtime에서 market/news/AI 수동 수집 smoke를 한 번에 계획하거나 실행하는 CLI다.

기본은 preview다. `--execute`를 붙이지 않으면 provider/API/DB write command를 실행하지 않는다.

## Preview

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke
```

이 명령은 다음만 출력한다.

- 실행할 job 목록
- redacted command argv
- runtime status 요약
- artifact root
- LaunchAgents/`launchctl`이 여전히 비활성인 이유

화면에서 이 결과를 보려면 repo 밖 summary 파일로도 남긴다.

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke \
  --output /private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json
```

FastAPI runtime에 아래 env를 설정하면 `/api/data-health`와 `/data-health`가 이 summary를 읽는다.

```bash
STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT=/private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json
```

## Execute

```bash
PYTHONPATH=src python3 -m stockanalysis.operations.cli manual-local-ingest-smoke --execute
```

`--execute`가 있을 때만 다음 jobs를 artifact runner로 실행한다.

- `market-price-daily`: 일봉 가격 수집
- `news-rss-daily`: 무료 RSS 뉴스 수집
- `event-intelligence-weekly`: 로컬 뉴스 cluster evidence 생성

각 job은 stdout/stderr/metadata artifact를 남긴다.

기본 Python은 `/private/tmp/stockanalysis-runtime/venv/bin/python`이 있으면 그 venv를 사용한다. 없으면 현재 interpreter를 사용하며, 필요하면 `--python-executable`로 명시한다.

## 보안 경계

- repo-outside env file만 사용한다.
- env 값은 출력하지 않는다.
- command argv는 sensitive flag/value를 redact한다.
- `launchctl` 실행과 LaunchAgents write/delete는 하지 않는다.
- 실거래, broker order, write API는 범위 밖이다.

## 다음 단계

다음 작업은 실제 `--execute` smoke를 의도적으로 실행하고, 무료 provider quota와 DB write 결과가 `/data-health`에 반영되는지 확인하는 것이다.
