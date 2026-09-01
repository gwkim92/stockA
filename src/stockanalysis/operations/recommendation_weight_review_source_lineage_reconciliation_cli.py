from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from typing import Sequence

from stockanalysis.ingest.config import ConfigError, RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation import (
    run_recommendation_weight_review_source_lineage_reconciliation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockanalysis-weight-lineage-reconciliation",
        description=(
            "Reconcile the exact readiness-referenced recommendation quality/outcome lineage "
            "as a read-only shadow artifact."
        ),
    )
    parser.add_argument("--as-of-date", required=True, help="Audit date in YYYY-MM-DD format.")
    parser.add_argument(
        "--readiness-eval-run-id",
        type=int,
        help="Optional exact readiness audit eval_run_id. Otherwise latest valid readiness is selected.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Persist only the append-only reconciliation eval and pipeline-run lifecycle.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        as_of_date = date.fromisoformat(args.as_of_date)
        if args.readiness_eval_run_id is not None and args.readiness_eval_run_id <= 0:
            raise ValueError("readiness_eval_run_id must be greater than 0.")
        report = run_recommendation_weight_review_source_lineage_reconciliation(
            config=RuntimeConfig.from_env(),
            as_of_date=as_of_date,
            readiness_eval_run_id=args.readiness_eval_run_id,
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
