from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import date

from stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation import (
    build_recommendation_weight_review_prospective_evidence_foundation,
)


AUDIT_DATE = date(2026, 7, 15)


class FakeExecutor:
    def __init__(self, bundle: dict[str, object] | None = None) -> None:
        self.bundle = copy.deepcopy(bundle or _bundle())
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if "insert into ops.pipeline_run" in lowered:
            return "9901"
        if "insert into ai.eval_run" in lowered:
            return "8901"
        if "prospective evidence foundation v1 atomic lookup" in lowered:
            return json.dumps(self.bundle)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:200]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


def _build(bundle: dict[str, object]) -> dict[str, object]:
    return build_recommendation_weight_review_prospective_evidence_foundation(
        as_of_date=AUDIT_DATE,
        bundle=bundle,
    )


def _bundle() -> dict[str, object]:
    quality_score = {
        "as_of_date": "2026-07-15",
        "horizon_days": 365,
        "quality_status": "ready_for_weight_review",
        "recommendation_count": 2,
        "outcome_count": 2,
    }
    outcome_score = {
        "as_of_date": "2026-07-15",
        "horizon_days": [30, 90],
        "status": "ready_for_manual_weight_review",
        "sample_audit_after": {
            "summary": {
                "recommendation_count": 2,
                "outcome_count": 2,
            },
            "horizon_coverage": [
                {"horizon_day": 30, "outcome_count": 2},
                {"horizon_day": 90, "outcome_count": 0},
            ],
        },
    }
    feedback_run_1_items = [
        _feedback_item(
            decision_index=1,
            symbol="AAA",
            related_recommendation_id="recommendation-1",
            feedback_status="validated",
            outcome_id=101,
            recommendation_id=1,
            outcome_end_date="2026-07-01",
            latest_trade_date="2026-07-15",
        ),
        _feedback_item(
            decision_index=2,
            symbol="BBB",
            related_recommendation_id="recommendation-2",
            feedback_status="too_early",
            outcome_id=None,
            recommendation_id=None,
            outcome_end_date=None,
            latest_trade_date=None,
        ),
    ]
    feedback_run_2_items = [
        copy.deepcopy(feedback_run_1_items[0]),
        _feedback_item(
            decision_index=2,
            symbol="BBB",
            related_recommendation_id="recommendation-2",
            feedback_status="validated",
            outcome_id=None,
            recommendation_id=None,
            outcome_end_date=None,
            latest_trade_date="2026-07-15",
        ),
    ]
    return {
        "lineage": _wrapper(
            501,
            "recommendation_weight_review_source_lineage_reconciliation_v1",
            "recommendation-weight-review-source-lineage-reconciliation-v1",
            {
                "status": "reconciled_read_only",
                "lineage_reconciled": True,
                "canonical_chain": _canonical_chain(),
                "cohort_filter_identity": {
                    "required_filters": {
                        "market_code": "US",
                        "strategy_name": "long_term",
                        "horizon_type": "calendar_days",
                        "universe_version": "professional-us-v1",
                    }
                },
            },
        ),
        "referenced_quality": _wrapper(
            301,
            "recommendation_quality_calibration",
            "recommendation-quality-live-v1",
            quality_score,
        ),
        "referenced_outcome": _wrapper(
            201,
            "recommendation_outcome_calibration_sample_expansion",
            "recommendation-outcome-calibration-sample-expansion-v1",
            outcome_score,
        ),
        "recommendations": [
            _recommendation(
                recommendation_id=1,
                batch_id=11,
                instrument_id=101,
                symbol="AAA",
                batch_as_of_date="2026-06-01",
                rank=1,
            ),
            _recommendation(
                recommendation_id=2,
                batch_id=12,
                instrument_id=102,
                symbol="BBB",
                batch_as_of_date="2026-06-10",
                rank=2,
            ),
        ],
        "outcomes": [
            _outcome(
                outcome_id=101,
                recommendation_id=1,
                start_date="2026-06-01",
                end_date="2026-07-01",
                horizon_days=30,
            ),
            _outcome(
                outcome_id=102,
                recommendation_id=2,
                start_date="2026-06-10",
                end_date="2026-07-10",
                horizon_days=30,
            ),
        ],
        "feedback_calibration": _wrapper(
            601,
            "portfolio_review_feedback_calibration",
            "portfolio-review-feedback-calibration-v1",
            {
                "as_of_date": "2026-07-15",
                "portfolio_name": "Long Term Paper",
                "feedback_run_count": 2,
                "decision_count": 4,
                "latest_feedback_runs": [
                    {"eval_run_id": 7002},
                    {"eval_run_id": 7001},
                ],
            },
        ),
        "feedback_artifacts": [
            _wrapper(
                7002,
                "portfolio_review_decision_outcome_feedback",
                "portfolio-review-decision-outcome-feedback-v1",
                {
                    "as_of_date": "2026-07-15",
                    "portfolio_name": "Long Term Paper",
                    "source_history_eval_run_id": 8001,
                    "source_history_as_of_date": "2026-06-15",
                    "items": feedback_run_2_items,
                },
                created_at="2026-07-15T13:00:00Z",
            ),
            _wrapper(
                7001,
                "portfolio_review_decision_outcome_feedback",
                "portfolio-review-decision-outcome-feedback-v1",
                {
                    "as_of_date": "2026-07-14",
                    "portfolio_name": "Long Term Paper",
                    "source_history_eval_run_id": 8001,
                    "source_history_as_of_date": "2026-06-15",
                    "items": feedback_run_1_items,
                },
                created_at="2026-07-14T13:00:00Z",
            ),
        ],
    }


def _canonical_chain() -> dict[str, object]:
    payload: dict[str, object] = {
        "contract_version": "recommendation-weight-review-source-lineage-v1",
        "as_of_date": "2026-07-15",
        "quality": {"eval_run_id": 301},
        "outcome": {"eval_run_id": 201},
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return {
        **payload,
        "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
    }


def _wrapper(
    eval_run_id: int,
    eval_name: str,
    dataset_version: str,
    score_json: dict[str, object],
    *,
    created_at: str = "2026-07-15T12:00:00Z",
) -> dict[str, object]:
    return {
        "eval_run_id": eval_run_id,
        "eval_name": eval_name,
        "dataset_version": dataset_version,
        "provider": "postgres",
        "model_name": "deterministic-test-v1",
        "score_json": copy.deepcopy(score_json),
        "created_at": created_at,
    }


def _recommendation(
    *,
    recommendation_id: int,
    batch_id: int,
    instrument_id: int,
    symbol: str,
    batch_as_of_date: str,
    rank: int,
) -> dict[str, object]:
    return {
        "recommendation_id": recommendation_id,
        "batch_id": batch_id,
        "instrument_id": instrument_id,
        "primary_symbol": symbol,
        "thesis_id": recommendation_id + 1000,
        "bucket": "core",
        "action": "hold",
        "rank_position": rank,
        "total_score": "0.75",
        "recommended_weight": "0.10",
        "status": "active",
        "batch_as_of_date": batch_as_of_date,
        "market_code": "US",
        "strategy_name": "long_term",
        "horizon_type": "calendar_days",
        "universe_version": "professional-us-v1",
        "batch_source_run_id": 9000 + recommendation_id,
        "batch_created_at": f"{batch_as_of_date}T12:00:00Z",
        "components": [
            {
                "component_name": "momentum_score",
                "component_score": "0.60",
                "component_weight": "0.25",
                "explanation": "momentum",
                "created_at": f"{batch_as_of_date}T12:01:00Z",
            },
            {
                "component_name": "valuation_margin_score",
                "component_score": "0.40",
                "component_weight": "0",
                "explanation": "protected zero-weight component",
                "created_at": f"{batch_as_of_date}T12:01:00Z",
            },
        ],
    }


def _outcome(
    *,
    outcome_id: int,
    recommendation_id: int,
    start_date: str,
    end_date: str,
    horizon_days: int,
) -> dict[str, object]:
    return {
        "outcome_id": outcome_id,
        "recommendation_id": recommendation_id,
        "measurement_start_date": start_date,
        "measurement_end_date": end_date,
        "horizon_days": horizon_days,
        "entry_price": "100",
        "exit_price": "110",
        "absolute_return_pct": "0.10",
        "benchmark_code": "SPY",
        "benchmark_return_pct": "0.05",
        "alpha_pct": "0.05",
        "max_drawdown_pct": "-0.03",
        "outcome_label": "positive",
        "source_run_id": 9100 + outcome_id,
        "created_at": f"{end_date}T12:00:00Z",
    }


def _feedback_item(
    *,
    decision_index: int,
    symbol: str,
    related_recommendation_id: str,
    feedback_status: str,
    outcome_id: int | None,
    recommendation_id: int | None,
    outcome_end_date: str | None,
    latest_trade_date: str | None,
) -> dict[str, object]:
    recommendation_outcome: dict[str, object] = {}
    if outcome_id is not None:
        recommendation_outcome = {
            "outcome_id": outcome_id,
            "recommendation_id": recommendation_id,
            "measurement_end_date": outcome_end_date,
        }
    return {
        "decision_index": decision_index,
        "decision_family": "position_sizing",
        "symbol": symbol,
        "decision_type": "hold_review",
        "source_decision": {
            "related_recommendation_id": related_recommendation_id,
            "related_thesis_id": f"thesis-{1000 + decision_index}",
        },
        "feedback_status": feedback_status,
        "feedback_reason": f"{feedback_status} evidence",
        "evidence": {
            "recommendation_outcome": recommendation_outcome,
            "thesis_outcome": {},
            "price_evidence": (
                {"latest_trade_date": latest_trade_date}
                if latest_trade_date is not None
                else {}
            ),
            "paper_validation": {"paper_validation_run_id": 77},
        },
    }


def _blocker_codes(result: dict[str, object]) -> set[str]:
    blockers = result["blockers"]
    assert isinstance(blockers, list)
    return {
        str(item.get("code"))
        for item in blockers
        if isinstance(item, dict)
    }


def _contains_write(sql: str) -> bool:
    return bool(
        re.search(
            r"\b(insert\s+into|update\s+|delete\s+from|truncate\s+)\b",
            sql,
            flags=re.IGNORECASE,
        )
    )
