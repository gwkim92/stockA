# Verification checkpoints

Initial feature head 83ca215141d194bfd4da9145dff97e747bbda841 ran Web Product Quality 34077422329, job 101606166626. The observed log shows 472 unit tests across 36 files, including 29 new review-continuity cases; all passed. Locked installation and both existing dependency audit gates passed. Production build compilation passed but its TypeScript phase failed with TS7053 in ReviewContinuity: a compound union's status could still include direct when indexing failure-only copy. No browser tests executed in this failed run and none are counted as passed.

The follow-up binds the status literal before excluding loaded/direct and indexing copy. This is a type-safe explicit branch, not an any cast, typecheck suppression or weakened test. Head 5c00eb988499ebf07decb0f313e20feae4541823 / run 34077631844 passed unit, production build and generated-route typecheck before the safety refinement below; that checkpoint is not final verification.

## Protect already-open edits on later read failure

Review found a lifecycle risk: after admitting a verified same-instrument editor, reloading the comparison after the selected record disappears could unmount that editor and discard dirty in-memory text. The updated component retains an already-admitted editor only for that exact selected/current instrument. Initial missing/corrupt/denied/mismatched references still do not mount it. The unchanged editor's own cross-tab conflict and compare-before-save logic continue to block recreation/overwrite. Explicitly opening a different current context is not offered as a shortcut while retained unsaved edits exist.

Two additional browser cases cover external deletion -> failed comparison reload -> preserved dirty text and export with no record recreation, and same-tab save -> unchanged comparison baseline until explicit reload. The caption now distinguishes the loaded comparison baseline from later editor saves. No localStorage writer, new format, model call or source-validation claim is introduced.

Final-head build and browser evidence remains required. Local runtime and manual image review remain unavailable; CI captures are not visually inspected merely because generated. All original suites and assertions remain enabled.
