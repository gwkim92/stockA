# Analysis prompt contract v1

User request: continue stockA development and inspect its prompts. Base: develop@e6ae966d4cdd0aafd03446c3674b4eb6fd62e23f (PR #34 already merged; post-merge Web Product Quality run 33974167198 was verified successful). This corrects the previous chat report that stopped at PR #33.

## Goal

Audit actual runtime prompt builders, their input projections, provider adapters and output validators. Improve the existing investment research workflow at the point where source material becomes interpreted evidence, not by adding another display-only gate. Inventory runtime prompt families and separate operational/developer instructions from model analysis instructions.

## Scope and acceptance

Identify concrete, reproducible deficiencies before editing. Prioritize source-versus-instruction separation, exact supplied identifiers, missing/future/conflicting evidence, units/currency/date semantics, abstention, fact-versus-hypothesis separation, output schema compatibility, and preventing model text from authorizing scoring/portfolio/order changes. Preserve useful domain analysis: causal mechanisms, catalysts, disconfirming evidence and review conditions.

Make bounded prompt/validation changes with offline regression cases and an explicit prompt version change where the existing runtime supports it. Keep existing golden evaluation criteria and scoring weights unchanged. Test exact prompt assembly and malformed/adversarial outputs, not just keyword presence. Record prompts inspected, issues fixed, uncovered limitations and final commit/CI evidence. No live paid model call is authorized by this task; deterministic checks are not proof of model accuracy or injection immunity.

## Boundaries

No main, database access/mutation or replacement database, schema/migrations, benchmark/evaluation split or golden-set changes, scoring weights, portfolio/order/broker execution, account/production secrets/AWS, scheduler or deployment configuration, dependency/lockfile changes. Preserve existing runtime/provider selection. A temporary read-only tracked-source export may be used for the DNS-restricted sandbox and removed before integration; no secrets, .git credentials or runtime artifacts are exported. Persistent CI remains read-only.

The newest user instruction explicitly prioritizes prompt inspection over another unrelated page redesign. Integrate only a tested final head into develop. Actual EC2 data, live model quality and deployment remain separately unverified. Maintain a final audit and handoff in this task directory.
