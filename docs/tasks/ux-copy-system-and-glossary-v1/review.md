# ux-copy-system-and-glossary-v1 Review

## Review Notes

- Replaced prominent user-facing `weight`, `broker submit`, `artifact`, `validator`, `taxonomy`, and `Codex OAuth` wording across home, news/AI, recommendations, stocks, portfolio coverage, and trading readiness copy.
- Replaced visible “사람이 검토” wording where there is no actual review write action.
- Preserved blocker semantics and read-only/no-order boundaries.
- Did not change backend DTOs, recommendation scoring weights, benchmark definitions, portfolio positions, paper execution, broker submit, or order flow.
- Deployed to EC2 and smoke checked seven high-traffic routes through both EC2 internal `:3000` and local tunnel `:13000`.
