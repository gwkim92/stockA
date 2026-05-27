# alert-destination-free-channel-v1 Review

## Review Notes

- The runner is generic and secret-free. It never writes destination URLs or tokens to stdout, report JSON, data-health, or frontend UI.
- `ntfy` is supported as a free no-account option via repo-outside env.
- The gate is still evidence-based: a configured target alone is not enough; a recent `last_test_status=passed` artifact is required.

## Remaining Risk

- Public no-auth ntfy topics should be treated as secrets because anyone with the topic can publish/subscribe.

## EC2 Result

- commit `56dff0d` deployed to `/opt/stockanalysis/app`.
- repo-outside ntfy target configured without printing the URL.
- execute smoke passed and wrote `/opt/stockanalysis/artifacts/alert-destination/status.json`.
- `alert_destination` is no longer in `/api/data-health.open_gates`.
- Remaining open gate is `portfolio_review_feedback_calibration_attention`.
