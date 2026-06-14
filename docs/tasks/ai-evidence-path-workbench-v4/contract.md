# ai-evidence-path-workbench-v4 Contract

## Task Request

- request: Continue the AI evidence UX refactor by making `/ai-evidence/[id]`, `/ai-evidence/blocked`, and `/ai-evidence/results` readable as one evidence path.
- context: The pages already expose source news, AI output, validator state, and recommendation links, but the same concepts are spread across repeated cards. A user still needs a fixed reading order and clearer Korean wording.

## Goal

- goal: Each AI evidence page should answer `what happened`, `why it passed or failed`, `where it connects`, and `whether it can affect recommendation/order` without requiring the user to decode technical logs.

## Scope

- Include:
  - add a reusable AI evidence path workbench component.
  - apply the workbench to `/ai-evidence/[evidenceId]`, `/ai-evidence/results`, and `/ai-evidence/blocked`.
  - clarify Korean copy for source, translation, AI structure, validator, propagation/recommendation linkage, and order boundary.
  - improve CSS and responsive layout for the workbench.
  - local and route smoke verification.
- Exclude:
  - backend schema changes.
  - AI prompt/model changes.
  - recommendation scoring or weight changes.
  - portfolio/benchmark mutation.
  - broker/order flow.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/ai-evidence/_components/*`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/ai-evidence-path-workbench-v4/*`

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-evidence-path-workbench-v4`
- verification command: route smoke for `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, and at least one `/ai-evidence/[id]`

## Acceptance Criteria

- The top half of each target page exposes the same evidence path: source news, Korean translation, AI structure, validator result, recommendation/order boundary.
- `blocked` clearly says these rows are excluded from recommendation inputs unless taxonomy/alias remediation is needed.
- `results` separates passed direct-stock evidence, macro/theme evidence, and cluster evidence without implying automatic trade execution.
- detail page prioritizes the final use verdict and one trace path before lower-level metadata.
- No scoring, recommendation weight, benchmark, portfolio position, or broker/order mutation is introduced.
