# Session Handoff

## Current Status

- 진행 중: 홈 뉴스 정보 구조 분리 작업을 시작했다.
- 기준일: 2026-05-22

## Investigation

- 홈 기능 지도에서 `수집 뉴스 원장`과 `1차 분류 태그`가 모두 `/events`로 연결돼 있었다.
- `분석 목록`, `차단 후보`, `통과 결과`도 `/ai-evidence`와 anchor 중심이라 사용자가 같은 화면으로 느낄 수밖에 없었다.
- `/events` 자체도 원장, 직접 후보, 상위 흐름 후보, 관련 이벤트를 한 화면에 섞어 “무엇을 먼저 봐야 하는지”가 흐려져 있었다.

## Exact Next Step

- exact next step: split news ledger, classification tags, structured results, and blocked candidates into dedicated frontend routes.
