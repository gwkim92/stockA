# Session Handoff

## Current Status

- 상태: in_progress
- in progress: 뉴스/원천 문서 검토 화면을 한국어 우선으로 바꾼다.
- 기준일: 2026-05-23

## Findings

- `NewsTitleBlock`은 영어 뉴스 제목을 `원문 제목`으로 먼저 보여준다.
- `원천 문서 검토서`도 발췌 summary가 영어면 그대로 보여준다.
- 현재 DB에는 완전한 한국어 번역 컬럼이 없으므로, 이번 단계는 구조화된 종목/테마/방향/영향도 기반 한국어 검토 요약을 기본값으로 보여주고 영어 원문은 접어두는 방식이 현실적이다.

## Exact Next Step

- exact next step: `NewsTitleBlock`을 한국어 우선 표시로 바꾸고, 원천 문서 상세에 한국어 검토 요약/영어 원문 접기 UI를 추가한다.
