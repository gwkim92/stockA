# Session Handoff

## Current Status

- 상태: in_progress
- in progress: `/intelligence` 페이지를 사람이 실제로 검토를 시작할 수 있는 구조로 정리한다.
- 기준일: 2026-05-23

## Findings

- 기존 페이지는 뉴스 처리 흐름, 상세 링크, 판단 보드, 개별 후보가 모두 길게 이어져 첫 행동이 보이지 않았다.
- “사람 검토”라는 표현은 있었지만 검토 시작 버튼과 검토 기준이 명확하지 않았다.
- 현재 backend/API는 read-only라서 검토 완료/반려 저장 버튼은 구현 범위 밖이다. 이 제한을 화면에서 명확히 설명해야 한다.

## Exact Next Step

- exact next step: `/intelligence` 상단에 검토 시작판을 추가하고, 뉴스 묶음/개별 후보 CTA와 체크리스트를 정리한다.
