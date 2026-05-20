# Local Ingest Worker Data Health Visibility

생성일: 2026-05-20

## 목적

로컬 worker 실행 상태를 수동 smoke summary와 분리해서 `/data-health`에서 확인한다.

## 표시되는 정보

- worker status
- 실제 실행 여부
- 생성 시각
- 완료 cycle 수
- 실패 cycle 수
- 실행 대상 job id
- 최신 smoke summary 경로
- 다음 조치

## 경계

- 이 작업은 visibility만 추가한다.
- scheduler 설치나 `launchctl` 실행은 하지 않는다.
- API/화면에는 secret 값, DB URL, token, raw env 값을 노출하지 않는다.
