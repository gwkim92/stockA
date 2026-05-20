# Local Ingest Worker Loop

생성일: 2026-05-20

## 목적

수동으로 검증된 market/news/AI local ingest smoke를 Mac LaunchAgents 없이 로컬 process worker로 반복 실행할 수 있게 한다.

## 운영 모델

- 기본 실행은 preview 1회다. provider/API/DB write를 하지 않는다.
- 실제 실행은 `--execute`가 있어야 한다.
- 반복은 `--max-cycles N`으로 bounded 처리한다.
- `--smoke-output /private/tmp/.../manual-local-ingest-smoke.json`을 지정하면 각 cycle의 최신 smoke summary가 repo 밖 파일로 갱신되고, 기존 `/data-health`가 그 파일을 읽어 최신 수집/분석 증거를 보여줄 수 있다.

## 경계

- 이 작업은 scheduler 설치가 아니다.
- `launchctl`, LaunchAgents write/delete, external VPS/managed scheduler activation은 하지 않는다.
- 유료 LLM, 추천 점수 변경, DB schema 변경, broker/order flow도 범위 밖이다.
