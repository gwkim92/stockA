# Session Handoff

## Current Status

- 완료: 홈 뉴스 정보 구조를 분리하고 EC2에 배포했다.
- 기준일: 2026-05-22

## Investigation

- 홈 기능 지도에서 `수집 뉴스 원장`과 `1차 분류 태그`가 모두 `/events`로 연결돼 있었다.
- `분석 목록`, `차단 후보`, `통과 결과`도 `/ai-evidence`와 anchor 중심이라 사용자가 같은 화면으로 느낄 수밖에 없었다.
- `/events` 자체도 원장, 직접 후보, 상위 흐름 후보, 관련 이벤트를 한 화면에 섞어 “무엇을 먼저 봐야 하는지”가 흐려져 있었다.

## 완료

- 완료: `/events`를 수집 뉴스 원장 전용 화면으로 단순화했다.
- 완료: `/events/classification` 1차 분류 태그 화면을 추가했다.
- 완료: `/ai-evidence/results` 구조화 결과 화면을 추가했다.
- 완료: `/ai-evidence/blocked` 차단 후보 화면을 추가했다.
- 완료: 홈 기능 지도 링크를 새 전용 화면으로 연결했다.
- 완료: EC2 `127.0.0.1:13000` 경로에서 `/`, `/events`, `/events/classification`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/intelligence`가 200으로 렌더링됨을 확인했다.

## Exact Next Step

- exact next step: continue taxonomy hardening for remaining weak RSS classifications and improve wording on recommendation/thesis pages.
