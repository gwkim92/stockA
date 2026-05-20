# Session Handoff

## Active Task

- 이름: operating-data-profile-scheduler
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - `stockanalysis-operations operating-data-run`에 `--profile` option을 추가했다.
  - `full-recovery`는 전체 복구/배포 smoke용으로 유지했다.
  - 자동 운영 후보 profile을 분리했다.
  - `news-intraday`: RSS 수집, RSS 이벤트 enrichment, 뉴스 클러스터 AI evidence.
  - `market-daily`: 무료 provider budget을 지키는 market candle watchlist refresh.
  - `decision-daily`: missing symbol backfill, cycle/recommendation/thesis, portfolio snapshot, remediation, paper validation.
  - `macro-weekly`: macro series refresh.
  - `performance-monthly`: due performance outcome schedule.
  - 뉴스/AI 관련 cadence를 intraday로 노출하고 `news_rss_event_enrichment` expected job을 cadence registry에 추가했다.
  - `news-intraday`는 portfolio positions CSV 없이 preview할 수 있게 dependency를 분리했다.

## Exact Next Step

- 다음 세션은 이것부터 시작: EC2 systemd timer 배포 전에 profile별 timer plan을 만든다. 같은 backend command를 사용하되 `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, `performance-monthly`를 별도 service/timer로 나누고, `full-recovery`는 manual-only로 남긴다.

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_operating_data_orchestrator tests.test_data_operations_cli tests.test_data_operations_cadence -v`

## Risks

- 아직 EC2 systemd timer는 설치하지 않았다.
- `event-intelligence-weekly` job id는 기존 호환을 위해 유지하지만 cadence와 command template은 intraday local cluster evidence 방향으로 정렬했다.
- 실거래 broker submission과 kill switch unlock은 여전히 범위 밖이다.
