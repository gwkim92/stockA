# Future Server-Side Scheduler Architecture

생성일: 2026-05-20

## 결론

이 문서는 **나중에 외부 운영 자동화가 필요해졌을 때** 사용할 server-side scheduler 선택지다.

현재 immediate direction은 `local-first-runtime-direction`이다. 먼저 내 Mac에서 Local Postgres, `stockanalysis-operations` worker, FastAPI read-only API, Next.js cockpit이 안정적으로 돌아야 한다.

Mac `launchd`는 local-first 단계에서 “내 컴퓨터에서도 매일 돌릴 수 있는지” 확인하기 위한 선택 옵션이다. 외부 서버 scheduler는 노트북이 꺼져도 매일 수집되어야 하거나 외부 운영 접속이 필요할 때 다시 선택한다.

## 왜 웹 서버 안에서 직접 돌리지 않는가

FastAPI/Next.js 요청 서버 안에 scheduler를 넣지 않는다.

- 웹 서버는 사용자가 페이지를 열 때 빠르게 응답해야 한다.
- 서버가 여러 대가 되면 같은 scheduler가 중복 실행될 수 있다.
- 배포/재시작 때 background job 상태가 꼬일 수 있다.
- 오래 걸리는 수집/분석 작업은 request timeout과 충돌한다.
- 실패 재시도, 로그, artifact, alert 책임이 웹 요청 처리와 섞인다.

따라서 웹 서버는 읽기 API, worker는 데이터 작업, scheduler는 실행 시각과 재시도를 담당한다.

## 미래 외부 운영 구조

```text
Next.js cockpit
  -> FastAPI read-only API
    -> Postgres canonical tables
      <- stockanalysis-operations worker
        <- external/server-side scheduler
```

역할은 다음처럼 나눈다.

- `Next.js`: 운영자가 보는 화면
- `FastAPI`: read-only DTO 제공, health/readiness, auth boundary
- `Postgres`: canonical state, pipeline run history, portfolio/signal/performance tables
- `stockanalysis-operations`: macro, market price, news, SEC, AI evidence, review, outcome jobs 실행
- External/server-side scheduler: 일간/주간/월간 cadence에 맞춰 operations job 호출
- Artifact/log storage: stdout, stderr, metadata, LLM/event evidence, 실패 원인 저장

## 외부 scheduler 후보

외부 운영이 필요해질 때 첫 후보는 “가벼운 external scheduler가 `stockanalysis-operations`를 호출”하는 구조다.

가능한 배치 방식:

- 단일 VPS 또는 NAS: `systemd timer` 또는 cron이 worker command 실행
- Container host: scheduler container가 정해진 시간에 worker container command 실행
- GitHub Actions scheduled workflow: public repo 기반 무료/저비용 smoke나 낮은 빈도 job 후보
- Managed cron/platform scheduler: 배포 플랫폼의 scheduled job 기능

중요한 점은 scheduler 구현체가 아니라 interface다. 어떤 scheduler를 쓰든 최종적으로 아래 boundary를 호출해야 한다.

```bash
stockanalysis-operations run --job-id <job-id> -- <job command...>
```

또는 job별 convenience command를 호출한다.

```bash
stockanalysis-operations market-price-daily-run --skip-if-fresh
stockanalysis-operations news-rss-daily-run
stockanalysis-operations news-rss-enrich-run
stockanalysis-operations news-rss-cluster-evidence-run
```

## Job Cadence

현재 운영상 필요한 cadence는 다음이다.

- 일간: `market-price-daily`, `news-rss-daily`, `portfolio-position-daily`, `portfolio-remediation-daily`
- 주간: `macro-weekly`, `sec-filings-weekly`, `event-intelligence-weekly`, `cycle-state-weekly`
- 월간: `performance-outcome-monthly`, `portfolio-attribution-monthly`

실제 배포 전에는 각 job이 다음을 만족해야 한다.

- repo 밖 env file만 사용한다.
- stdout/stderr/metadata artifact를 남긴다.
- `ops.pipeline_run` 또는 equivalent run history에 상태를 남긴다.
- 실패 시 재시도/알림이 가능해야 한다.
- API quota가 있는 provider는 budget ledger를 먼저 확인한다.

## Data Health가 보여야 할 상태

`/data-health`는 다음을 구분해서 보여줘야 한다.

- 최근 단발 실행 성공 여부
- 주기 scheduler가 실제 배포되어 있는지
- scheduler가 어떤 provider quota를 쓰는지
- 마지막 성공/실패 시각
- stale dataset
- 다음 조치

외부 운영으로 전환하기 전의 현재 상태는 “최근 실행 성공, 반복 실행 미설정”이다.

## Mac LaunchAgents의 위치

Mac `LaunchAgents`는 최종 운영 경로가 아니다.

허용되는 용도:

- 로컬 live MVP 검증
- operator 개인 개발 환경에서의 임시 반복 실행
- 서버 배포 전 scheduler command preview 검증

외부 운영으로 전환할 때는 server-side scheduler로 대체할 수 있다.

## 보안 경계

- secret은 repo에 저장하지 않는다.
- `.env`는 repo 밖 경로를 사용한다.
- 브라우저/Next public env에 token을 노출하지 않는다.
- scheduler는 write API나 broker order를 직접 호출하지 않는다.
- 실거래는 broker boundary, account permission, order limit, kill switch, audit log, explicit approval 이후 별도 범위다.

## 외부 운영이 필요해질 때의 구현 순서

1. server scheduler deployment target을 고른다.
2. `stockanalysis-operations` job matrix를 server scheduler용 manifest로 정리한다.
3. job별 env readiness를 repo-outside runtime file 기준으로 검증한다.
4. scheduler가 artifact runner를 통해 job을 실행하게 한다.
5. `/data-health`가 server scheduler deployment status와 latest run artifact를 읽게 한다.
6. 실패/timeout/stale alert를 연결한다.

## 현재 결정

외부 server scheduler 선택은 보류한다.

다음 고정 방향은 `local-first-runtime-direction`이다. 먼저 로컬 실행 순서, local runtime status, 수동 ingest smoke, `/data-health` 반영을 완성한다.
