# Implementation Plan

1. Create the runtime DB smoke verification script.
2. Reuse the existing deterministic fixture pipeline to build DB state.
3. Start the frontend runtime in live production-profile read-token mode.
4. Assert public health, unauthorized rejection, and authorized live DTO reads.
5. Update docs and current-task references.
6. Run smoke, roadmap, AWH, unit, placeholder, and diff checks.
