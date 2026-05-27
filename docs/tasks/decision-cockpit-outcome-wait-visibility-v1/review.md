# decision-cockpit-outcome-wait-visibility-v1 Review

## Review Notes

- Added a home page outcome wait section using existing `/api/data-health.outcome_maturity_wait_monitor`.
- The home page now shows recommendation outcome due date, portfolio feedback maturity date, weight review boundary, and read-only order boundary before the generic status rail.
- This is visibility-only. Recommendation weights, benchmark definitions, portfolio positions, broker submit, and order flow remain unchanged.
- EC2 and local tunnel smoke confirmed the new home copy renders live.
