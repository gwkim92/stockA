# Execution plan and scope adjustment

Base develop@04c6c3799625f2d808e256ca219b097ddc990f34. Continue PR #35's concrete prompt findings rather than another unrelated UI redesign.

1. Reproduce numeric and source-boundary defects with saved fixtures and adversarial inputs before changing runtime behavior.
2. Validate the unchanged SEC output schema at parsing and canonical candidate construction; preserve zero and the existing threshold. Check input budget types and source/chunk identity.
3. Apply the shared source-data framing to the separate Codex translation and news-structuring builders. Distinguish literal original spans from Korean explanation, and validate those spans in SDK, Codex and injected-provider pipeline paths.
4. Run negative and positive pipeline tests using fake executors. Confirm invalid data cannot become a successful extraction/translation write, while supported source evidence still passes the existing gates.
5. Inspect final allowed-change diff, run the existing guarded CI on Python 3.11 and 3.13 with the optional SDK installed, inspect artifacts, then integrate only the tested head into develop.

## Scope adjustment caused by a blocked write

The equity-research change was prepared and tested locally, but the ordinary GitHub tree upload was denied twice because the tool could not determine its security status. It was not uploaded through another route, delegated to a runner, relocated to another module or otherwise applied. The final branch retains the baseline equity runtime and tests. Consequently the equity zero-confidence/defaulting and input-cap findings remain open; this task is only a partial completion of the initial broader contract.

Independent SEC, translation and news-structuring changes succeeded through the authorized GitHub connector. A separate local worktree was assembled from only those accepted changes before counting verification results. Local results for the larger, unapplied equity experiment are not used as final branch evidence.
