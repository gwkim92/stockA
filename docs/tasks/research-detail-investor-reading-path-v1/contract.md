# research-detail-investor-reading-path-v1 Contract

## Task Request

- request: 남은 리서치 상세 화면의 UX/UI 문구와 정보구조를 투자자가 읽는 순서 중심으로 정리한다.
- context: `decision-surface-language-density-v1`은 주요 판단 화면의 밀도와 내부 용어를 정리했다. 다음 문제는 원천 문서, AI evidence 상세, 종목 상세가 아직 `AI 해석`, `AI 근거`, `이 화면은` 같은 내부/방어형 표현을 사용한다는 점이다.

## Goal

- goal: 원천 문서, 투자 근거 상세, 종목 상세가 `결론 → 원천 → 해석 → 종목/추천 연결 → 실거래 경계` 순서로 읽히고, 내부 분석 방식보다 투자자가 확인할 판단 포인트를 먼저 보여준다.

## Mutable Surface

- mutable surface: `apps/web/src/app/source-documents/[documentId]/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
- mutable surface: `apps/web/src/app/ai-evidence/_components/evidence-path-workbench.tsx`
- mutable surface: `apps/web/src/app/stocks/[symbol]/page.tsx`
- mutable surface: `docs/tasks/research-detail-investor-reading-path-v1/*`

## Invariants

- Do not change API contracts, database schema, scheduler cadence, scoring weights, benchmark definitions, portfolio positions, paper records, broker/order boundary, or live trading.
- Do not hide source limitations, blocked evidence, read-only order boundary, or stale/missing data.
- Keep operational/debug wording in `/data-health` and `/admin/ai-agents` out of scope.

## Scope

- Replace user-facing `AI 해석`, `AI 근거`, `AI가 참고한`, `이 화면은 ... 아니다` style copy with investor-facing evidence language.
- Tighten page hero/section text so each screen explains what to decide next.
- Keep existing links, data fields, evidence trace, and route structure intact.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task research-detail-investor-reading-path-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] `/source-documents/[id]` presents source verification as investor evidence, not AI-process inspection.
- [ ] `/ai-evidence/[id]` presents the evidence usage path without `AI 해석` wording.
- [ ] `/stocks/[symbol]` source/evidence buttons and source sections use `투자 근거` / `근거 상세` language.
- [ ] Local verification passes.
