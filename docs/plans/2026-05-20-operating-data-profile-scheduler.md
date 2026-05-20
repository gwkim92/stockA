# Operating Data Profile Scheduler Plan

## Summary

- `operating-data-run`은 full recovery용 전체 runner로 유지하되, 자동 운영은 profile별로 쪼갠다.
- profile은 같은 backend boundary와 artifact runner를 사용하므로 shell script 확장을 피한다.
- 실제 systemd timer 설치는 다음 task로 남긴다.

## Profiles

- `news-intraday`: RSS 수집, 이벤트 enrichment, 뉴스 cluster evidence. 권장 주기 30-60분.
- `market-daily`: 주식 캔들 watchlist 보강. 권장 주기 장 마감 후 1회.
- `decision-daily`: 추천/신호/thesis/보유검토/paper validation. 권장 주기 market-daily 성공 후 1회.
- `macro-weekly`: 매크로 context. 권장 주기 주 1회.
- `performance-monthly`: matured thesis outcome readiness. 권장 주기 월 1회.
- `full-recovery`: 전체 실행. 권장 주기 없음, 수동 복구/배포 smoke 전용.

## Guardrails

- preview-first.
- repo-outside env/output/artifact paths.
- no broker submission.
- no scheduler host mutation in this task.
- no paid provider assumption.

## Verification

- focused unittest.
- orchestrator verification script.
- compileall.
- diff whitespace check.
