# Session Handoff

## Current Status

- 상태: in_progress
- 완료:
  - task contract를 만들었다.
  - `/ai-evidence/[evidenceId]`에 `EvidenceTracePath`를 추가했다.
  - 상단에서 `원천 뉴스 -> 한국어 번역 -> AI 구조화 -> validator 판정 -> 추천 연결` 경로를 5개 카드로 보여준다.
  - 원천 문서, 종목 상세, 추천 검토서가 있으면 trace card에서 직접 이동할 수 있다.
  - 차단 후보는 추천 입력으로 쓰지 않는다고 명확히 표시한다.
  - AI/validator/추천 로직은 변경하지 않았다.

## Verification So Far

- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.

## Exact Next Step

- exact next step: run `git diff --check` and AWH verify for `ai-evidence-review-visibility-v2`, then commit/push this slice.
- after EC2 SSH becomes reachable, deploy and visually smoke `/ai-evidence/<known-id>` through `http://127.0.0.1:13000`.
