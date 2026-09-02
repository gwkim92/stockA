from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Sequence

from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation import (
    DEFAULT_PORTFOLIO_NAME,
    run_recommendation_weight_review_prospective_evidence_foundation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-weight-prospective-evidence",
        description=(
            "Build a read-only recommendation row/component/outcome/feedback identity "
            "foundation anchored to an exact reconciled source lineage."
        ),
    )
    parser.add_argument("--as-of-date", required=True, help="Audit date in YYYY-MM-DD format.")
    parser.add_argument(
        "--lineage-eval-run-id",
        type=int,
        help="Optional exact source-lineage reconciliation eval_run_id.",
    )
    parser.add_argument(
        "--portfolio-feedback-calibration-eval-run-id",
        type=int,
        help="Optional exact Long Term Paper feedback calibration eval_run_id.",
    )
    parser.add_argument(
        "--portfolio-name",
        default=DEFAULT_PORTFOLIO_NAME,
        help=f"Paper portfolio scope (default: {DEFAULT_PORTFOLIO_NAME}).",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Persist only the append-only foundation eval and pipeline-run lifecycle.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        as_of_date = date.fromisoformat(args.as_of_date)
        if args.lineage_eval_run_id is not None and args.lineage_eval_run_id <= 0:
            raise ValueError("lineage_eval_run_id must be greater than 0.")
        if (
            args.portfolio_feedback_calibration_eval_run_id is not None
            and args.portfolio_feedback_calibration_eval_run_id <= 0
        ):
            raise ValueError(
                "portfolio_feedback_calibration_eval_run_id must be greater than 0."
            )
        report = run_recommendation_weight_review_prospective_evidence_foundation(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            lineage_eval_run_id=args.lineage_eval_run_id,
            portfolio_feedback_calibration_eval_run_id=(
                args.portfolio_feedback_calibration_eval_run_id
            ),
            portfolio_name=args.portfolio_name,
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
