# Session Handoff

## Current Status

- 상태: in_progress
- 기준일: 2026-05-22
- 완료:
  - task contract를 생성했다.
  - EC2 실제 데이터에서 accepted `news_event_candidate` artifact 중 저신뢰 무종목 일반 뉴스가 남아 있음을 확인했다.
- 막힌 점:
  - 없음.

## Planned Fix

- 검증된 theme/instrument impact가 없는 AI output은 accepted `news_event_candidate`가 아니라 `news_event_candidate_rejected`로 저장한다.
- rejected artifact도 request hash 중복 조회에 포함해 같은 후보를 반복 호출하지 않게 한다.
- frontend event list의 candidate 품질 필터를 기존 MarketWatch 무종목 후보에서 일반 뉴스 source의 무종목·저신뢰 후보까지 확장한다.

## Verification Log

- pending

## Remaining

- acceptance gate 구현
- local verification
- EC2 deploy and smoke

## Exact Next Step

- exact next step: implement the runner artifact gate and frontend quality filter.
