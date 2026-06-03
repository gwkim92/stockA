# source-news-evidence-trace-wording-v1 Handoff

## Current Status

- in progress: local implementation is complete and verification is underway.

## Decisions

- This is a wording and evidence-trace clarity task only.
- Keep the existing page structure and API contracts.
- Use `AI 근거`, `AI 구조화`, `근거 상세`, `수집 목록`, `보유 상태`, and `가상 매매` consistently.
- Preserve validator and order-boundary language. Do not imply that source documents approve recommendations or orders.

## Changes

- `/events` now describes source news as a `수집 목록` and AI state as `AI 구조화`/`AI 근거`.
- `/events/classification` now describes tag review as `태그와 방향 확인` and AI comparison as `AI 근거와 비교`.
- `/source-documents/[documentId]` now presents the source page as `원천 문서 근거 상세`, with `한국어 근거 요약`, `근거 발췌`, and `AI 근거 연결`.
- `/ai-evidence/results` now uses `보유 상태`, `가상 매매`, and `근거 묶음` wording.
- `NewsEventCard` now labels unstructured items as `AI 구조화 전` and evidence links as `AI 근거 상세`.

## Verification

- passed: text scan found no `AI 판단`, `검토서`, `검수`, `보유검토`, `페이퍼`, `AI 증거`, `AI 후보`, `AI 분석 전`, `추천 승인`, `수집 원장`, `AI 분석 목록`, `원문 다운로드`, `검토 발췌`, `검토 요약`, `연결된 증거`, `원장 보기`, or `미검토` in the target route/component files.

## Next Step

- exact next step: run typecheck/build/backend smoke/AWH verify, then deploy to EC2 and smoke `/events`, `/events/classification`, `/ai-evidence/results`, and a representative source document route.
