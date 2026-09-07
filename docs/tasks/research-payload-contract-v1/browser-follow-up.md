# Browser verification follow-up

Candidate 4e185606ae5e6eb68c91eba4f75000457800368f / Web Product Quality 34084158275 did not complete the browser gate successfully. Its Python regression, frontend units, production build/type checks and audit stages passed. The later five browser suites were not executed after the notebook gate failed; they are not counted as passed for that candidate.

The new warning component used aside with role=status. It now uses a neutral div with role=status and explicit aria-atomic=true, retaining the same visible content and style. This follows the status-message element pattern in W3C WAI ARIA22 (https://www.w3.org/WAI/WCAG21/Techniques/aria/ARIA22). The accessibility assertion is retained and strengthened with explicit role/atomic checks. A passing axe result does not establish assistive-technology announcement timing in every browser.

Producer browser assertions now target the exact company or notebook workspace, not a global duplicate test ID that could match both during client navigation. They wait for the intended route/workspace after actual link clicks; no first-match shortcut, arbitrary delay, retry, hidden content or reduced accessibility rule set is introduced. Existing exact narrative, source-ID/no-fetch, missing-versus-empty and no-approval assertions remain.

This refinement does not change API payloads, financial/evaluation rules, runtime dependencies, original source identity handling, note persistence or any deployment setting. All prior suites remain mandatory. The next exact commit must pass the full workflow before integration. Manual pixel inspection and local execution remain unverified; CI screenshots alone do not close those boundaries.
