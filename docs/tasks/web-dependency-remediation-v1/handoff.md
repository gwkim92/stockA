# Frontend dependency remediation — handoff

## Implemented

Next 16.2.9 -> 16.3.4; postcss 8.4.31/8.5.15 -> deduplicated 8.5.23; sharp 0.34.5 -> 0.35.4; brace-expansion 5.0.6 -> 5.0.9; browserslist 4.28.4 -> 4.28.9; fast-uri 3.1.2 -> 3.1.7; nanoid 3.3.12 -> 3.3.18; undici 7.28.0 -> 7.29.1. Related Next/SWC, sharp platform binaries and browser metadata changed as required by their dependency ranges (54 lock entries including metadata). React/ReactDOM 19.2.5 and all unrelated direct dependency declarations stayed unchanged. No overrides or forced peer-range bypasses.

Upstream verification: vercel/next.js tag v16.3.4 packages/next/package.json directly pins postcss 8.5.23 and accepts sharp ^0.35.4. Maintainer Next advisory GHSA-6gpp-xcg3-4w24 identifies affected Next <16.2.11; postcss GHSA-fxqj-rqcc-2cmp is included in the captured initial audit. Transitive updates stay within installed parent ranges.

## Evidence

Preparation run 33945881443 at e6b92dcfc9f87b14bf1de6fd5ef32a009efc7537 completed successfully; generated commit ade90224ad938e62b4882fe0ac27d042292244fd modified only package.json/package-lock.json. Artifact 9963307459 contains exact tracked web source, before/after audit, production audit, upstream npm metadata and the 54-entry lock diff inventory.

2026-09-05 audit result: full dependency findings 8 high -> 0 total; production-only findings 0 after patch. This is the registry's observed advisory result, not a guarantee against unknown vulnerabilities. The clean install/build/type/unit/browser workflow must pass on the final committed PR head before merge. Live deployment/exploitability was not assessed.

## Persistent protection

Web Product Quality now fails on high/critical audit results and captures both full and production JSON. No continue-on-error for these gates. Persistent workflow permissions remain contents:read; checkout credentials are not persisted. The temporary branch-only lock generator has been removed from the final tree.

## Boundary

No deployment, production credentials, database, backend, financial model/weight, portfolio, order or broker changes. Track PR/CI outcome on issue #26 before closing. Recommendation detail work is a separate PR.
