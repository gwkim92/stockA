# Session Handoff

## Current Status

- 상태: implementing
- 기준일: 2026-05-22
- 완료:
  - 이전 패스에서 뉴스 원문/화면 해석 분리는 `/intelligence`, `/events`, `/ai-evidence`, `/stocks/[symbol]`에 적용됐다.
  - 이번 패스는 추천 상세와 원천 문서 상세까지 같은 기준을 확장한다.

## Page Review Notes

- TODO: route smoke 결과 기록.
- TODO: 남은 page/copy 우선순위 기록.

## Verification Log

- TODO: local typecheck/build.
- TODO: AWH verify.
- TODO: EC2 deploy and smoke.

## Exact Next Step

- exact next step: apply NewsTitleBlock to recommendation detail and source document detail, then run route smoke across all main pages.
