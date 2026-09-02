# recommendation-weight-review-prospective-evidence-live-observation-v1 Review

## Review Checklist

- database identity is evaluated before every domain read;
- exact IDs are mandatory and rendered into the foundation lookup;
- no independently selected latest source can replace them;
- legacy-surface projection includes source score hashes, recommendation scores/weights, component/outcome/feedback/cohort hashes, and permission boundaries;
- execute rereads the exact surface after the first allowed write;
- drift prevents final eval insertion;
- reports and score JSON exclude connection configuration and secrets;
- all pilot, mutation, order, and broker flags are false;
- no migration, deployment, or scheduler change is present.

## Expected Review Result

Approve only the observation plumbing. Do not interpret approval as authorization to connect an unverified target or run a weight pilot.
