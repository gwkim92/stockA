# Review

## Result

- AI 근거 상세에 상단 추적 경로를 추가했다.
- 사용자는 긴 상세 섹션을 읽기 전에 원천, 번역, AI 구조화, validator 판정, 추천 연결 상태를 순서대로 볼 수 있다.
- 추천 연결이 없을 때도 오류처럼 보이지 않고 `관찰 또는 상위 흐름 근거일 수 있다`고 설명한다.
- 한국어 번역이 있으면 trace에서 번역 신뢰도를 표시한다.

## Changed Surface

- `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- `apps/web/src/app/globals.css`
- `docs/tasks/ai-evidence-review-visibility-v2/*`

## Guardrails

- AI 재분석 실행 없음.
- validator 판정 로직 변경 없음.
- canonical event impact write 없음.
- 추천 scoring 변경 없음.
- 저장형 승인/반려 UI 없음.

## Remaining Risk

- EC2 SSH가 timeout이라 live tunnel visual smoke는 아직 못 했다.
- 실제 화면별 데이터 품질은 EC2 배포 후 대표 `ai-evidence` ID로 다시 확인해야 한다.
