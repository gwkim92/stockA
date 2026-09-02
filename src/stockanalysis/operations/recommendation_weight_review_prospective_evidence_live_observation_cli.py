from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Sequence

from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_contract import (
    DEFAULT_PORTFOLIO_NAME,
)
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_live_observation import (
    run_recommendation_weight_review_prospective_evidence_live_observation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-weight-prospective-evidence-live-observation",
        description=(
            "Run an exact-ID, append-only PostgreSQL observation of the prospective "
            "recommendation evidence foundation."
        ),
    )
    parser.add_argument(
        "--as-of-date",
        required=True,
        help="Observation date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--lineage-eval-run-id",
        type=int,
        required=True,
        help="Exact source-lineage reconciliation eval_run_id.",
    )
    parser.add_argument(
        "--portfolio-feedback-calibration-eval-run-id",
        type=int,
        required=True,
        help="Exact Long Term Paper feedback calibration eval_run_id.",
    )
    parser.add_argument(
        "--portfolio-name",
        default=DEFAULT_PORTFOLIO_NAME,
        help=f"Paper portfolio scope (default: {DEFAULT_PORTFOLIO_NAME}).",
    )
    parser.add_argument(
        "--environment-label",
        required=True,
        help="Non-secret operator label for the intended PostgreSQL target.",
    )
    parser.add_argument(
        "--expected-database-identity-sha256",
        required=True,
        help="Expected SHA-256 of the canonical database identity payload.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Write only one pipeline lifecycle and one append-only live-observation eval "
            "after the environment and legacy-surface checks pass."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_recommendation_weight_review_prospective_evidence_live_observation(
            config=RuntimeConfig.from_env(),
            as_of_date=date.fromisoformat(args.as_of_date),
            lineage_eval_run_id=args.lineage_eval_run_id,
            portfolio_feedback_calibration_eval_run_id=(
                args.portfolio_feedback_calibration_eval_run_id
            ),
            portfolio_name=args.portfolio_name,
            environment_label=args.environment_label,
            expected_database_identity_sha256=(
                args.expected_database_identity_sha256
            ),
            execute=bool(args.execute),
        )
    except (ConfigError, ValueError, RuntimeError) as exc:
        print(
            json.dumps(
                {
                    "error": {
                        "code": exc.__class__.__name__,
                        "message": str(exc),
                    }
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0


def main_entry() -> None:
    raise SystemExit(main())


if __name__ == "__main__":
    main_entry()
