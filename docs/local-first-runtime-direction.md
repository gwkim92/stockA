# Local-First Runtime Direction

생성일: 2026-05-20

## 결론

지금 프로젝트의 즉시 목표는 외부 서버 배포가 아니라 **local-first 투자 운영 시스템**이다.

즉, 먼저 내 Mac에서 다음이 안정적으로 돌아야 한다.

```text
Local Postgres
  <- stockanalysis-operations worker/CLI
  -> FastAPI read-only API
  -> Next.js cockpit
  -> Browser
```

외부 VPS, GitHub Actions scheduler, managed cron, server-side scheduler는 나중에 “노트북이 꺼져도 계속 돌려야 할 때” 선택한다.

## 서버라는 말의 구분

혼동을 피하기 위해 `서버`를 세 종류로 나눈다.

- 화면 서버: Next.js dev/prod server. 브라우저 화면을 보기 위한 로컬 프로세스다.
- 읽기 API 서버: FastAPI read-only backend. Next.js가 DB를 직접 읽지 않도록 DTO 경계를 제공하는 로컬 프로세스다.
- 운영 배포 서버: VPS, container host, GitHub Actions, managed scheduler 같은 외부 실행 환경이다.

현재 필요한 것은 첫 번째와 두 번째다. 세 번째는 지금 즉시 필수 조건이 아니다.

## 그래도 FastAPI/Next가 필요한 이유

굳이 외부 서버를 띄우지 않아도 웹 화면을 보려면 로컬에서 Next.js 프로세스는 떠야 한다. 그리고 Next.js가 DB schema에 직접 묶이면 화면 변경과 데이터 경계가 섞이므로 FastAPI read-only API를 둔다.

이 구조는 외부 배포 없이도 유효하다.

- 로컬 브라우저에서 cockpit을 본다.
- FastAPI는 local loopback에서만 읽기 API를 제공한다.
- DB secret과 read token은 브라우저에 노출하지 않는다.
- 수집/분석 job은 웹 요청 서버 안에서 돌리지 않고 `stockanalysis-operations` worker/CLI가 실행한다.

## 실행 모드

### 1. 수동 로컬 실행

가장 먼저 완성해야 하는 모드다.

- 사용자가 필요할 때 데이터 수집 command를 실행한다.
- 실행 결과는 Postgres와 artifact root에 남는다.
- `/data-health`가 최신 수집 상태를 보여준다.
- 실패하면 화면과 artifact에서 원인을 확인한다.

### 2. 로컬 반복 실행

수동 실행이 안정되면 선택한다.

- Mac `launchd`, cron, 또는 간단한 로컬 runner가 `stockanalysis-operations`를 호출한다.
- 이 모드는 개인 개발/운영 편의 기능이다.
- 실제 `launchctl` 실행이나 LaunchAgents 쓰기는 명시 승인 전까지 하지 않는다.

### 3. 외부 운영 자동화

나중에 필요할 때 선택한다.

- 노트북이 꺼져도 매일 수집되어야 할 때
- 외부에서 cockpit을 접속해야 할 때
- 알림, 재시도, 로그 보존, 백업이 중요해질 때

이때 server-side scheduler 문서를 다시 꺼내면 된다.

## 현재 우선순위

1. local runtime 상태를 한눈에 확인한다.
2. local Postgres, FastAPI, Next, operations worker 실행 순서를 단순화한다.
3. 주식 캔들, 뉴스, AI evidence job을 수동으로 돌리고 `/data-health`에서 확인한다.
4. 반복 실행은 local runner 옵션으로만 준비한다.
5. 외부 server scheduler 배포는 보류한다.

## 보안 경계

- secret은 repo에 저장하지 않는다.
- `.env`와 runtime env는 repo 밖 파일을 우선한다.
- Next public env에 token을 노출하지 않는다.
- 웹 요청 서버가 broker/order/write job을 직접 실행하지 않는다.
- 실거래는 broker boundary, account permission, order limit, kill switch, audit log, explicit approval 이후 별도 범위다.

## 다음 구현 순서

다음 구현은 외부 배포 manifest가 아니라 local one-command run/status orchestration이다.

- local runtime status report. Implemented in `local-runtime-status-orchestrator`.
- local FastAPI/Next/Postgres 연결 확인
- operations worker command matrix
- 수동 data ingest smoke
- `/data-health`에서 local runner 상태 표시
- 선택 사항으로 local 반복 실행 preview
