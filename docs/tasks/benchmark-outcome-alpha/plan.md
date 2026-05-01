# Plan

- performance verify 전용 SEC universe fixture에 SPY benchmark instrument를 추가한다.
- SPY daily adjusted fixture를 추가해 2024-11-01부터 2024-11-04까지 benchmark return `0.005000`을 만든다.
- outcome unit test에 benchmark return `0.005000`, alpha `0.005000`, label `outperform` 경로를 추가한다.
- Docker verify에서 SPY price가 수집기 경로로 적재되도록 하고 DB assertion을 alpha 기준으로 바꾼다.
- performance 문서와 verification plan, task handoff/review를 갱신한다.
