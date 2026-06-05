from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.frontend.live_adapter import (
    FrontendLiveUnavailableError,
    FrontendLiveUnsupportedPathError,
    _attach_portfolio_review_feedback_maturity_visibility,
    _apply_portfolio_review_feedback_managed_wait_policy,
    _build_alert_destination_payload,
    _build_auth_rbac_payload,
    _build_benchmark_rebalance_candidate_review_payload,
    _build_data_operations_artifact_runner_payload,
    _build_financial_statement_model_payload,
    _build_fund_instrument_analysis_payload,
    _build_portfolio_review_feedback_cadence_payload,
    _build_portfolio_review_feedback_calibration_payload,
    _build_production_api_server_payload,
    _build_professional_source_guardrail_payload,
    _benchmark_drift_quality_attention_policy,
    _portfolio_review_decision_history_attention_policy,
    _professional_source_gap_requires_attention,
    _resolve_data_health_overall_status,
    _build_recommendation_evidence_review_payload,
    _build_recommendation_outcome_due_action_router_payload,
    _build_recommendation_outcome_maturity_payload,
    _build_recommendation_professional_decision_waterfall_payload,
    _build_recommendation_professional_evidence_audit_payload,
    is_live_supported_path,
    render_frontend_ai_news_cluster_list_state_sql,
    render_frontend_ai_evidence_detail_state_sql,
    render_frontend_cycle_map_state_sql,
    render_frontend_cycle_state_list_sql,
    render_frontend_event_list_state_sql,
    render_frontend_market_map_state_sql,
    render_frontend_paper_trading_preview_state_sql,
    render_frontend_portfolio_concentration_state_sql,
    render_frontend_portfolio_position_sizing_context_state_sql,
    render_frontend_portfolio_review_feedback_action_router_state_sql,
    render_frontend_portfolio_review_feedback_cadence_state_sql,
    render_frontend_portfolio_review_feedback_calibration_state_sql,
    render_frontend_portfolio_review_decision_feedback_state_sql,
    render_frontend_portfolio_review_decision_history_state_sql,
    render_frontend_recommendation_list_state_sql,
    render_frontend_recommendation_detail_state_sql,
    render_frontend_source_document_detail_state_sql,
    render_frontend_stock_detail_state_sql,
    render_frontend_stock_list_state_sql,
    render_frontend_theme_detail_state_sql,
    render_frontend_thesis_detail_state_sql,
    render_frontend_trading_readiness_state_sql,
    resolve_live_frontend_response,
)
from stockanalysis.frontend.pagination import encode_frontend_cursor


class FakeLiveExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- frontend dashboard state lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "as_of_date": "2024-11-01",
                    "daily_automation": "succeeded",
                    "latest_run_id": 9101,
                    "failed_pipeline_count": 0,
                    "open_ticket_count": 1,
                    "critical_blind_spot_count": 1,
                    "missing_thesis_count": 1,
                    "missing_outcome_count": 0,
                    "top_actions": [
                        {
                            "symbol": "BABA",
                            "action": "needs_thesis_review",
                            "reason": "coverage status missing_thesis",
                            "suggested_runner": "thesis_or_position_link_review",
                            "risk_level": "high",
                        }
                    ],
                    "latest_metrics": {
                        "covered_weight": "0.0500",
                        "missing_thesis_weight": "0.0300",
                        "cash_weight": "0.9200",
                        "weight_coverage_ratio": "0.6250",
                    },
                }
            )
        if sql.startswith("-- frontend data health state lookup"):
            return json.dumps(
                {
                    "overall_status": "attention_required",
                    "as_of_date": "2024-11-01",
                    "pipeline_runs": [
                        {
                            "pipeline_name": "portfolio_remediation_daily_automation",
                            "job_id": "portfolio-remediation-daily",
                            "domain": "portfolio",
                            "cadence": "daily",
                            "expected_after_local": "19:00",
                            "stale_after_hours": 36,
                            "artifact_policy": "stdout_json_stderr_log_and_summary_link",
                            "latest_status": "succeeded",
                            "health_status": "ok",
                            "latest_run_id": 9101,
                            "finished_at": "2024-11-01T23:30:00+00:00",
                        }
                    ],
                    "latest_artifact_root": "",
                    "freshness": [
                        {
                            "dataset": "market.daily_price_bar",
                            "status": "observed",
                            "latest_observation_date": "2024-12-02",
                        },
                        {
                            "dataset": "portfolio.position_snapshot",
                            "status": "observed",
                            "latest_observation_date": "2024-11-01",
                        },
                    ],
                    "active_recommendation_price_freshness": {
                        "status": "stale_prices",
                        "attention_required": True,
                        "active_symbol_count": 2,
                        "fresh_symbol_count": 1,
                        "stale_symbol_count": 1,
                        "missing_symbol_count": 0,
                        "stale_recommendation_count": 3,
                        "missing_recommendation_count": 0,
                        "global_latest_trade_date": "2024-12-02",
                        "stale_after_days": 7,
                        "max_days_behind_latest": 9,
                        "stale_symbols": [
                            {
                                "symbol": "QUBT",
                                "instrument_id": 7002,
                                "instrument_name": "Quantum Computing Inc.",
                                "status": "stale",
                                "latest_trade_date": "2024-11-23",
                                "global_latest_trade_date": "2024-12-02",
                                "days_behind_latest": 9,
                                "active_recommendation_count": 3,
                                "latest_recommendation_date": "2024-11-25",
                                "detail_href": "/stocks/QUBT",
                            }
                        ],
                        "next_action": "active 추천 종목 watchlist로 market-price-free-backfill-run을 실행한다.",
                        "recommendation_scoring_mutated": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "news_ai_eval_quality": {
                        "status": "passed",
                        "eval_run_id": 72,
                        "created_at": "2026-05-27T07:00:00+00:00",
                        "eval_name": "news_ai_extraction_quality",
                        "dataset_version": "news-ai-eval-v1",
                        "provider": "fixture",
                        "model_name": "news-ai-eval-fixture-v1",
                        "overall_pass": True,
                        "case_count": 5,
                        "passed_case_count": 5,
                        "failed_case_count": 0,
                        "theme_precision": "1.0",
                        "direct_ticker_grounding_precision": "1.0",
                        "macro_only_false_ticker_rate": "0.0",
                        "macro_only_false_ticker_count": 0,
                        "quantum_energy_misclassification_count": 0,
                        "blocked_candidate_correctness": "1.0",
                        "korean_translation_availability": "1.0",
                        "metrics": {
                            "case_count": 5,
                            "failed_case_count": 0,
                            "theme_precision": 1.0,
                            "direct_ticker_grounding_precision": 1.0,
                            "macro_only_false_ticker_count": 0,
                            "quantum_energy_misclassification_count": 0,
                            "korean_translation_availability": 1.0,
                        },
                        "pass_thresholds": {"theme_precision_min": 1.0},
                        "case_results": [
                            {
                                "case_id": "quantum_policy_not_energy",
                                "category": "quantum_policy",
                                "passed": True,
                                "accepted_theme_codes": ["QUANTUM_COMPUTING_POLICY"],
                                "accepted_direct_symbols": ["QUBT"],
                                "missing_theme_codes": [],
                                "missing_direct_symbols": [],
                                "forbidden_theme_hits": [],
                                "forbidden_symbol_hits": [],
                                "blocked_symbols_accepted": [],
                                "rejected_impact_count": 1,
                                "translation_available": True,
                            }
                        ],
                        "next_action": "뉴스 AI 회귀평가가 통과했다.",
                    },
                    "live_ai_invocation_health": {
                        "status": "healthy",
                        "window_hours": 48,
                        "recent_invocation_count": 12,
                        "recent_success_count": 12,
                        "recent_failed_count": 0,
                        "critical_failed_count": 0,
                        "critical_success_count": 10,
                        "latest_invocation_at": "2026-05-31T16:01:46+00:00",
                        "latest_failed_at": "",
                        "latest_failed_task_name": "",
                        "latest_error_summary": "",
                        "latest_error_code": "",
                        "task_health": [
                            {
                                "task_name": "news-rss-ai-extract",
                                "label": "뉴스 AI 구조화",
                                "critical": True,
                                "recent_invocation_count": 10,
                                "recent_success_count": 10,
                                "recent_failed_count": 0,
                                "latest_status": "succeeded",
                                "latest_created_at": "2026-05-31T16:01:46+00:00",
                                "latest_error_summary": "",
                                "latest_error_code": "",
                            },
                            {
                                "task_name": "cycle-community-ai-summary-v2",
                                "label": "사이클 흐름 요약",
                                "critical": False,
                                "recent_invocation_count": 2,
                                "recent_success_count": 2,
                                "recent_failed_count": 0,
                                "latest_status": "succeeded",
                                "latest_created_at": "2026-05-31T15:01:46+00:00",
                                "latest_error_summary": "",
                                "latest_error_code": "",
                            },
                        ],
                        "next_action": "최근 실제 Codex OAuth 호출이 성공했다.",
                    },
                    "portfolio_risk_budget_guardrail": {
                        "status": "loaded",
                        "eval_run_id": 22,
                        "as_of_date": "2026-05-25",
                        "effective_snapshot_date": "2026-05-23",
                        "risk_gate_decision": "blocked_by_risk_budget_review",
                        "blocking_reasons": [{"code": "sector_over_limit"}],
                        "warning_reasons": [{"code": "benchmark_composition_partial"}],
                        "benchmark_drift": {
                            "status": "calculated_partial_composition",
                            "benchmark_code": "SPY",
                            "benchmark_source": "operator_spy_holdings_2026_05_25",
                            "source_type": "operator_upload",
                            "source_as_of_date": "2026-05-25",
                            "drift_calculated": True,
                            "component_count": 4,
                            "composition_coverage_weight": "0.21500000",
                            "active_share": "0.39250000",
                            "total_absolute_drift": "0.78500000",
                            "top_active_positions": [
                                {
                                    "symbol": "MSFT",
                                    "portfolio_weight": "0.30780000",
                                    "benchmark_weight": "0.06500000",
                                    "active_weight": "0.24280000",
                                }
                            ],
                        },
                    },
                    "portfolio_review_decision_history": {
                        "status": "loaded",
                        "eval_run_id": 52,
                        "created_at": "2026-05-27T02:00:00+00:00",
                        "eval_name": "portfolio_review_decision_history",
                        "dataset_version": "portfolio-review-decision-history-v1",
                        "as_of_date": "2026-05-25",
                        "portfolio_name": "Long Term Paper",
                        "source_portfolio_coverage_as_of_date": "2026-05-25",
                        "coverage_measurement_end_date": "2026-06-25",
                        "decision_status": "review_required",
                        "decision_count": 2,
                        "review_required_count": 2,
                        "benchmark_decision_count": 1,
                        "position_sizing_decision_count": 1,
                        "decision_counts": {"reduce_watch": 1, "add_blocked_until_evidence": 1},
                        "top_decision": {
                            "decision_family": "benchmark_drift",
                            "symbol": "MSFT",
                            "priority": 1,
                            "decision_type": "reduce_watch",
                            "decision_label": "비중 축소 검토",
                            "next_review_action": "추가 매수를 막고 축소 여부만 검토한다.",
                            "severity": "high",
                            "current_weight": "0.3078",
                            "benchmark_weight": "0.0650",
                            "active_weight": "0.2428",
                            "source_evidence": {"benchmark_code": "SPY"},
                            "related_thesis_id": "thesis-7001",
                            "related_recommendation_id": "recommendation-7101",
                            "links": {"stock": "/stocks/MSFT", "recommendation": "/recommendations/recommendation-7101"},
                            "decision_path": [],
                            "rationale": "MSFT active weight가 크다.",
                            "review_required": True,
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        },
                        "latest_decisions": [
                            {
                                "decision_family": "benchmark_drift",
                                "symbol": "MSFT",
                                "priority": 1,
                                "decision_type": "reduce_watch",
                                "decision_label": "비중 축소 검토",
                                "next_review_action": "추가 매수를 막고 축소 여부만 검토한다.",
                                "severity": "high",
                                "current_weight": "0.3078",
                                "benchmark_weight": "0.0650",
                                "active_weight": "0.2428",
                                "source_evidence": {"benchmark_code": "SPY"},
                                "related_thesis_id": "thesis-7001",
                                "related_recommendation_id": "recommendation-7101",
                                "links": {"stock": "/stocks/MSFT", "recommendation": "/recommendations/recommendation-7101"},
                                "decision_path": [],
                                "rationale": "MSFT active weight가 크다.",
                                "review_required": True,
                                "automatic_order_allowed": False,
                                "broker_submit_allowed": False,
                                "order_boundary": "read_only_no_order",
                            }
                        ],
                        "guardrails": {
                            "recommendation_scoring_mutated": False,
                            "benchmark_definition_mutated": False,
                            "portfolio_position_mutated": False,
                            "automatic_rebalance_allowed": False,
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        },
                        "next_action": "최신 포트폴리오 검토 결정을 확인한다.",
                    },
                    "portfolio_review_decision_feedback": {
                        "status": "loaded",
                        "eval_run_id": 53,
                        "created_at": "2026-05-27T03:00:00+00:00",
                        "eval_name": "portfolio_review_decision_outcome_feedback",
                        "dataset_version": "portfolio-review-decision-outcome-feedback-v1",
                        "as_of_date": "2026-05-27",
                        "portfolio_name": "Long Term Paper",
                        "source_history_eval_run_id": 52,
                        "source_history_as_of_date": "2026-05-25",
                        "min_horizon_days": 30,
                        "history_age_days": 2,
                        "feedback_status": "too_early",
                        "decision_count": 1,
                        "too_early_count": 1,
                        "validated_count": 0,
                        "contradicted_count": 0,
                        "needs_more_data_count": 0,
                        "status_counts": {"too_early": 1},
                        "paper_validation": {"status": "missing", "conflict_count": 0},
                        "top_feedback": {
                            "decision_index": 1,
                            "decision_family": "benchmark_drift",
                            "symbol": "MSFT",
                            "decision_type": "reduce_watch",
                            "decision_label": "비중 축소 검토",
                            "feedback_status": "too_early",
                            "feedback_reason": "30일 최소 관찰 기간이 아직 끝나지 않았다.",
                            "source_decision": {
                                "priority": 1,
                                "severity": "high",
                                "current_weight": "0.3078",
                                "benchmark_weight": "0.0650",
                                "active_weight": "0.2428",
                                "related_recommendation_id": "recommendation-7101",
                                "related_thesis_id": "thesis-7001",
                                "rationale": "MSFT active weight가 크다.",
                            },
                            "evidence": {
                                "recommendation_outcome": {},
                                "thesis": {"status": "active"},
                                "thesis_outcome": {},
                                "price_evidence": {},
                                "paper_validation": {"status": "missing", "conflict_count": 0},
                            },
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        },
                        "latest_items": [],
                        "guardrails": {
                            "recommendation_scoring_mutated": False,
                            "benchmark_definition_mutated": False,
                            "portfolio_position_mutated": False,
                            "automatic_rebalance_allowed": False,
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        },
                        "next_action": "성과 측정 window가 끝날 때까지 기다린다.",
                    },
                    "portfolio_review_feedback_calibration": {
                        "status": "loaded",
                        "eval_run_id": 54,
                        "created_at": "2026-05-27T04:00:00+00:00",
                        "eval_name": "portfolio_review_feedback_calibration",
                        "dataset_version": "portfolio-review-feedback-calibration-v1",
                        "as_of_date": "2026-05-27",
                        "portfolio_name": "Long Term Paper",
                        "lookback_days": 365,
                        "min_feedback_runs": 3,
                        "min_mature_decisions": 10,
                        "max_contradiction_rate": "0.15",
                        "calibration_status": "insufficient_history",
                        "feedback_run_count": 1,
                        "decision_count": 1,
                        "mature_decision_count": 0,
                        "too_early_count": 1,
                        "validated_count": 0,
                        "contradicted_count": 0,
                        "needs_more_data_count": 0,
                        "contradiction_rate": "0.0",
                        "validated_rate": "0.0",
                        "status_counts": {"too_early": 1},
                        "family_summaries": [
                            {
                                "decision_family": "benchmark_drift",
                                "decision_count": 1,
                                "mature_decision_count": 0,
                                "too_early_count": 1,
                                "validated_count": 0,
                                "contradicted_count": 0,
                                "needs_more_data_count": 0,
                                "contradiction_rate": "0.0",
                                "status_counts": {"too_early": 1},
                            }
                        ],
                        "decision_type_summaries": [],
                        "symbol_summaries": [
                            {
                                "symbol": "MSFT",
                                "decision_count": 1,
                                "mature_decision_count": 0,
                                "too_early_count": 1,
                                "validated_count": 0,
                                "contradicted_count": 0,
                                "needs_more_data_count": 0,
                                "contradiction_rate": "0.0",
                                "status_counts": {"too_early": 1},
                            }
                        ],
                        "latest_feedback_runs": [
                            {
                                "eval_run_id": 53,
                                "created_at": "2026-05-27T03:00:00+00:00",
                                "as_of_date": "2026-05-27",
                                "feedback_status": "too_early",
                                "decision_count": 1,
                                "too_early_count": 1,
                                "validated_count": 0,
                                "contradicted_count": 0,
                                "needs_more_data_count": 0,
                            }
                        ],
                        "guardrails": {
                            "recommendation_scoring_mutated": False,
                            "benchmark_definition_mutated": False,
                            "portfolio_position_mutated": False,
                            "automatic_rebalance_allowed": False,
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        },
                        "next_action": "feedback을 더 쌓는다.",
                    },
                    "portfolio_review_feedback_cadence": {
                        "status": "loaded",
                        "eval_run_id": 55,
                        "created_at": "2026-05-27T05:00:00+00:00",
                        "eval_name": "portfolio_review_feedback_cadence",
                        "dataset_version": "portfolio-review-feedback-cadence-v1",
                        "as_of_date": "2026-05-27",
                        "portfolio_name": "Long Term Paper",
                        "min_horizon_days": 30,
                        "cadence_status": "wait_for_outcome_window",
                        "action_type": "wait",
                        "should_run_now": False,
                        "should_wait": True,
                        "wait_until": "2026-06-24",
                        "command": "성과 window가 닫힌 뒤 다시 cadence를 계산한다.",
                        "follow_up_command": "",
                        "label": "성과 관찰 기간 대기",
                        "reason": "최신 검토 이력이 아직 최소 30일 관찰 기간을 채우지 못했다.",
                        "history": {
                            "status": "loaded",
                            "eval_run_id": 52,
                            "as_of_date": "2026-05-25",
                            "decision_count": 2,
                        },
                        "feedback": {
                            "status": "loaded",
                            "eval_run_id": 53,
                            "feedback_status": "too_early",
                            "source_history_eval_run_id": 52,
                        },
                        "calibration": {
                            "status": "loaded",
                            "eval_run_id": 54,
                            "calibration_status": "insufficient_history",
                            "latest_feedback_runs": [{"eval_run_id": 53}],
                        },
                        "evidence": {
                            "history_age_days": 2,
                            "decision_count": 2,
                            "recommendation_outcome_count": 0,
                            "price_evidence_count": 2,
                            "paper_validation": {
                                "paper_validation_run_id": 12,
                                "validation_date": "2026-05-27",
                                "status": "completed",
                                "recommendation_count": 2,
                                "conflict_count": 0,
                                "approved_action_count": 0,
                            },
                        },
                        "blocks_weight_review": True,
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                        "next_action": "성과 관찰 기간이 끝난 뒤 feedback과 calibration을 다시 판단한다.",
                    },
                    "portfolio_review_feedback_action_router": {
                        "status": "loaded",
                        "eval_run_id": 56,
                        "created_at": "2026-05-27T06:00:00+00:00",
                        "eval_name": "portfolio_review_feedback_action_router",
                        "dataset_version": "portfolio-review-feedback-action-router-v1",
                        "as_of_date": "2026-05-27",
                        "portfolio_name": "Long Term Paper",
                        "source_cadence_status": "loaded",
                        "source_cadence_eval_run_id": 55,
                        "source_cadence_created_at": "2026-05-27T05:00:00+00:00",
                        "source_cadence_as_of_date": "2026-05-27",
                        "cadence_status": "wait_for_outcome_window",
                        "source_action_type": "wait",
                        "source_should_run_now": False,
                        "route_action": "no_op",
                        "action_status": "no_op_wait_for_outcome_window",
                        "reason": "decision history has not reached the minimum outcome observation window.",
                        "history_eval_run_id": 52,
                        "feedback_eval_run_id": 53,
                        "calibration_eval_run_id": 54,
                        "source_cadence": {
                            "as_of_date": "2026-05-27",
                            "cadence_status": "wait_for_outcome_window",
                            "action_type": "wait",
                            "should_run_now": False,
                            "should_wait": True,
                            "command": "성과 window가 닫힌 뒤 다시 cadence를 계산한다.",
                            "follow_up_command": "",
                        },
                        "child_runner": {
                            "executed": False,
                            "report_name": "",
                            "status": "not_run",
                            "run_id": None,
                            "eval_run_id": None,
                        },
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                        "next_action": "성과 관찰 기간이 끝날 때까지 기다린다.",
                    },
                    "recommendation_outcome_calibration": {
                        "status": "loaded",
                        "eval_run_id": 31,
                        "created_at": "2026-05-27T00:00:00+00:00",
                        "as_of_date": "2026-05-27",
                        "horizon_days": [30, 90],
                        "calibration_status": "collect_more_outcomes_keep_weights",
                        "quality_status": "needs_more_data",
                        "sample_status": "insufficient_sample",
                        "recommendation_horizon_count": 12,
                        "recommendation_count": 6,
                        "outcome_count": 4,
                        "outcome_coverage_rate": "0.333333",
                        "ready_for_backfill_count": 2,
                        "missing_entry_price_count": 1,
                        "missing_exit_price_count": 0,
                        "missing_reason_counts": {
                            "outcome_recorded": 4,
                            "ready_for_backfill": 2,
                            "missing_entry_price": 1,
                        },
                        "component_diagnostic_count": 5,
                        "next_action": "성과 표본을 더 쌓는다.",
                        "recommendation_scoring_mutated": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "recommendation_outcome_maturity": {
                        "status": "not_due",
                        "as_of_date": "2026-05-27",
                        "source_calibration_eval_run_id": 31,
                        "horizon_days": [30, 90],
                        "recommendation_horizon_count": 12,
                        "recommendation_count": 6,
                        "outcome_count": 4,
                        "not_due_count": 5,
                        "ready_for_backfill_count": 2,
                        "due_today_count": 1,
                        "overdue_count": 1,
                        "price_gap_count": 1,
                        "missing_entry_price_count": 1,
                        "missing_exit_price_count": 0,
                        "next_due_date": "2026-06-01",
                        "next_due_count": 3,
                        "examples": [
                            {
                                "primary_symbol": "AAPL",
                                "recommendation_id": 147,
                                "as_of_date": "2026-05-02",
                                "horizon_day": 30,
                                "expected_measurement_end_date": "2026-06-01",
                                "maturity_status": "not_due",
                            }
                        ],
                        "recommendation_scoring_mutated": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                    },
                    "recommendation_outcome_due_action_router": {
                        "status": "loaded",
                        "eval_run_id": 71,
                        "created_at": "2026-05-27T02:00:00+00:00",
                        "eval_name": "recommendation_outcome_due_action_router",
                        "dataset_version": "recommendation-outcome-due-action-router-v1",
                        "as_of_date": "2026-05-27",
                        "source_calibration_status": "loaded",
                        "source_calibration_eval_run_id": 31,
                        "source_calibration_created_at": "2026-05-27T00:00:00+00:00",
                        "source_calibration_summary": {
                            "status": "collect_more_outcomes_keep_weights",
                            "quality_status": "needs_more_data",
                            "sample_status": "insufficient_sample",
                        },
                        "route_action": "no_op",
                        "action_status": "no_op_wait_until_next_due_date",
                        "reason": "추천 성과 측정창이 아직 열리지 않았다.",
                        "wait_until": "2026-06-01",
                        "sample_audit_summary": {
                            "recommendation_horizon_count": 12,
                            "recommendation_count": 6,
                            "outcome_count": 4,
                            "ready_for_backfill_count": 0,
                            "not_due_count": 5,
                            "missing_entry_price_count": 0,
                            "missing_exit_price_count": 0,
                            "price_gap_count": 0,
                            "outcome_coverage_rate": "0.333333",
                        },
                        "missing_reason_counts": {"not_due": 5},
                        "missing_examples": [],
                        "child_runner": {
                            "executed": False,
                            "report_name": "",
                            "status": "not_run",
                            "run_id": None,
                            "eval_run_id": None,
                        },
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                        "next_action": "다음 daily cadence까지 outcome maturity를 모니터링한다.",
                    },
                    "recommendation_weight_review_readiness": {
                        "status": "loaded",
                        "eval_run_id": 41,
                        "created_at": "2026-05-27T01:00:00+00:00",
                        "decision": "blocked_by_outcome_calibration_no_due_outcome_window",
                        "manual_weight_review_allowed": False,
                        "source_quality_status": "ready_for_weight_review",
                        "source_eval_run_id": 26,
                        "outcome_calibration_status": "no_due_outcome_window",
                        "outcome_calibration_eval_run_id": 27,
                        "blocker_code": "blocked_by_outcome_calibration_no_due_outcome_window",
                        "blocker_message": "선택한 30/90/180/365일 성과 측정창이 아직 도래하지 않았다.",
                        "next_action": "horizon-grid 성과 calibration gate를 먼저 통과해야 한다.",
                        "automatic_weight_change_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                    },
                    "professional_source_gap_prioritization": {
                        "status": "source_blockers_present",
                        "as_of_date": "2026-05-27",
                        "gap_count": 2,
                        "high_priority_count": 1,
                        "source_blocker_count": 1,
                        "fund_not_applicable_count": 1,
                        "fund_source_gap_count": 0,
                        "coverage_gap_count": 0,
                        "top_priority_score": "81.2000",
                        "gaps": [
                            {
                                "priority_rank": 1,
                                "symbol": "EROK",
                                "instrument_id": 7001,
                                "instrument_name": "Ero Copper Corp.",
                                "instrument_type": "equity",
                                "product_type": "operating_company",
                                "gap_status": "source_blockers_present",
                                "priority_band": "high",
                                "priority_score": "81.2000",
                                "active_recommendation_count": 1,
                                "highest_recommendation_score": "0.6200",
                                "current_weight": "0.0410",
                                "max_recommended_weight": "0.0500",
                                "missing_layer_count": 5,
                                "missing_layers": [
                                    "financial_metric_normalized",
                                    "valuation_snapshot",
                                    "equity_research_artifact",
                                ],
                                "blocker_type": "source_blocker",
                                "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                                "source_run_id": 1503,
                                "source_status": "failed",
                                "source_observed_at": "2026-05-26T12:00:00+00:00",
                                "source_error_summary": "facts.us-gaap absent",
                                "raw_filing_decision_eval_run_id": 29,
                                "raw_filing_decision_created_at": "2026-05-27T00:00:00+00:00",
                                "raw_filing_decision_status": "durable_exclusion_until_periodic_filing",
                                "raw_filing_blocker_code": "ipo_prospectus_without_standard_periodic_financials",
                                "raw_filing_decision_summary": "prospectus 원천은 있지만 표준 periodic financial facts가 없다.",
                                "raw_filing_next_action": "첫 10-Q/10-K 또는 전용 parser 전까지 제외한다.",
                                "raw_filing_recheck_trigger": "new_10_q_or_10_k_or_20_f_filing",
                                "raw_filing_latest_prospectus_form_type": "424B4",
                                "raw_filing_latest_prospectus_filing_date": "2026-05-14",
                                "remediation_action": "raw filing 가능성을 확인했다. 첫 periodic filing 전까지 장기 재무 판단에서 제외한다.",
                                "remediation_command": "",
                                "detail_href": "/stocks/EROK",
                            },
                            {
                                "priority_rank": 2,
                                "symbol": "SPY",
                                "instrument_id": 7002,
                                "instrument_name": "SPDR S&P 500 ETF Trust",
                                "instrument_type": "etf",
                                "product_type": "fund_or_etf",
                                "gap_status": "fund_company_model_not_applicable",
                                "priority_band": "watch",
                                "priority_score": "13.5000",
                                "active_recommendation_count": 1,
                                "highest_recommendation_score": "0.8500",
                                "current_weight": "0.0000",
                                "max_recommended_weight": "0.1000",
                                "missing_layer_count": 0,
                                "missing_layers": [],
                                "blocker_type": "fund_not_applicable",
                                "blocker_code": "fund_company_financial_model_not_applicable",
                                "source_run_id": None,
                                "source_status": "not_applicable",
                                "source_observed_at": None,
                                "source_error_summary": "",
                                "remediation_action": "기업 재무 모델은 적용하지 않고 fund/ETF 분석 표면에서 검토한다.",
                                "remediation_command": "",
                                "detail_href": "/stocks/SPY",
                            },
                        ],
                        "next_action": "source blocker가 있는 종목부터 확인한다.",
                        "recommendation_scoring_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "professional_analysis_depth": {
                        "status": "source_limited",
                        "as_of_date": "2026-05-27",
                        "active_candidate_count": 2,
                        "complete_candidate_count": 1,
                        "source_blocked_count": 1,
                        "fund_like_candidate_count": 1,
                        "operating_company_candidate_count": 1,
                        "average_coverage_ratio": "0.7750",
                        "weakest_coverage_ratio": "0.5500",
                        "layer_coverage": [
                            {
                                "layer_key": "financial_metric_normalized",
                                "label": "재무 지표 정규화",
                                "expected_count": 1,
                                "available_count": 0,
                            },
                            {
                                "layer_key": "valuation_snapshot",
                                "label": "밸류에이션 스냅샷",
                                "expected_count": 1,
                                "available_count": 1,
                            },
                            {
                                "layer_key": "fund_source_layers",
                                "label": "ETF·펀드 원천",
                                "expected_count": 1,
                                "available_count": 1,
                            },
                        ],
                        "items": [
                            {
                                "rank": 1,
                                "symbol": "EROK",
                                "instrument_id": 7001,
                                "instrument_name": "Ero Copper Corp.",
                                "product_type": "operating_company",
                                "depth_status": "source_blocked",
                                "coverage_ratio": "0.5500",
                                "available_layer_count": 3,
                                "expected_layer_count": 8,
                                "missing_layer_count": 5,
                                "missing_layers": [
                                    "financial_metric_normalized",
                                    "valuation_snapshot",
                                    "equity_research_artifact",
                                ],
                                "blocker_type": "source_blocker",
                                "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                                "active_recommendation_count": 1,
                                "current_weight": "0.0410",
                                "remediation_action": "첫 periodic filing 전까지 전문 판단 입력에서 제외한다.",
                                "detail_href": "/stocks/EROK",
                            },
                            {
                                "rank": 2,
                                "symbol": "SPY",
                                "instrument_id": 7002,
                                "instrument_name": "SPDR S&P 500 ETF Trust",
                                "product_type": "fund_or_etf",
                                "depth_status": "complete",
                                "coverage_ratio": "1.0000",
                                "available_layer_count": 5,
                                "expected_layer_count": 5,
                                "missing_layer_count": 0,
                                "missing_layers": [],
                                "blocker_type": "fund_not_applicable",
                                "blocker_code": "fund_company_financial_model_not_applicable",
                                "active_recommendation_count": 1,
                                "current_weight": "0.0000",
                                "remediation_action": "fund/ETF 원천으로 검토한다.",
                                "detail_href": "/stocks/SPY",
                            },
                        ],
                        "recommendation_scoring_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "professional_recommendation_coverage_audit": {
                        "status": "source_limited",
                        "as_of_date": "2026-05-27",
                        "recommendation_count": 2,
                        "ready_for_review_count": 0,
                        "coverage_gap_count": 0,
                        "source_blocked_count": 1,
                        "paper_validation_pending_count": 1,
                        "average_coverage_ratio": "0.7750",
                        "items": [
                            {
                                "rank": 1,
                                "recommendation_id": 67,
                                "symbol": "EROK",
                                "instrument_id": 7001,
                                "instrument_name": "Ero Copper Corp.",
                                "product_type": "operating_company",
                                "recommendation_score": "0.6200",
                                "recommended_weight": "0.0300",
                                "recommendation_as_of_date": "2026-05-27",
                                "audit_status": "blocked_source",
                                "professional_decision_status": "blocked_source",
                                "coverage_ratio": "0.5500",
                                "available_layer_count": 3,
                                "expected_layer_count": 8,
                                "missing_layer_count": 5,
                                "missing_layers": ["financial_metric_normalized", "valuation_snapshot"],
                                "blocker_type": "source_blocker",
                                "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                                "has_active_thesis": True,
                                "paper_validation_status": "missing",
                                "paper_validation_run_id": None,
                                "paper_validation_date": "",
                                "layer_checks": [
                                    {"key": "financial_metric_normalized", "label": "재무 지표", "status": "missing"},
                                    {"key": "active_thesis", "label": "투자 논리", "status": "complete"},
                                ],
                                "remediation_action": "첫 periodic filing 전까지 전문 판단에서 제외한다.",
                                "detail_href": "/recommendations/recommendation-67",
                                "stock_href": "/stocks/EROK",
                                "order_boundary": "read_only_no_order",
                                "automatic_weight_change_allowed": False,
                                "automatic_order_allowed": False,
                                "broker_submit_allowed": False,
                            }
                        ],
                        "next_action": "source-blocked 추천은 제외한다.",
                        "recommendation_scoring_mutated": False,
                        "automatic_weight_change_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "open_gates": [
                        "production_api_server",
                        "auth_rbac",
                        "alert_destination",
                        "data_operations_artifact_runner",
                        "actual_db_backed_frontend_live_smoke",
                    ],
                }
            )
        if sql.startswith("-- frontend stock list state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-12-02",
                    "stock_count": 2,
                    "summary": {
                        "latest_price_date": "2024-12-02",
                        "priced_stock_count": 2,
                        "recommended_stock_count": 1,
                        "held_stock_count": 1,
                    },
                    "stocks": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "instrument_id": 501,
                            "market_code": "US",
                            "currency_code": "USD",
                            "latest_price": {
                                "trade_date": "2024-12-02",
                                "close": "240.0000",
                                "adjusted_close": "240.0000",
                                "volume": 50000000,
                                "change_pct": "0.0100",
                            },
                            "data_coverage": {
                                "bar_count": 31,
                                "first_trade_date": "2024-11-01",
                                "last_trade_date": "2024-12-02",
                            },
                            "recommendation": {
                                "recommendation_id": 7101,
                                "linked_thesis_id": 7001,
                                "action": "monitor_or_accumulate",
                                "score": "0.7800",
                                "status": "active",
                                "as_of_date": "2024-11-01",
                            },
                            "position": {
                                "portfolio_name": "Long Term Paper",
                                "snapshot_date": "2024-11-01",
                                "quantity": "10",
                                "weight": "0.0500",
                                "market_price": "223.0000",
                                "market_value": "2230.00",
                                "linked_thesis_id": 7001,
                            },
                        },
                        {
                            "symbol": "BABA",
                            "name": "Alibaba Group Holding Limited",
                            "instrument_id": 502,
                            "market_code": "US",
                            "currency_code": "USD",
                            "latest_price": {
                                "trade_date": "2024-12-02",
                                "close": "90.0000",
                                "adjusted_close": "90.0000",
                                "volume": 18000000,
                                "change_pct": "-0.0200",
                            },
                            "data_coverage": {
                                "bar_count": 31,
                                "first_trade_date": "2024-11-01",
                                "last_trade_date": "2024-12-02",
                            },
                            "recommendation": None,
                            "position": None,
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend stock detail state lookup"):
            return json.dumps(
                {
                    "symbol": "AAPL",
                    "name": "Apple Inc.",
                    "instrument_id": 501,
                    "market_code": "US",
                    "currency_code": "USD",
                    "as_of_date": "2024-12-02",
                    "latest_price": {
                        "trade_date": "2024-12-02",
                        "open": "238.0000",
                        "high": "242.0000",
                        "low": "237.0000",
                        "close": "240.0000",
                        "adjusted_close": "240.0000",
                        "volume": 50000000,
                    },
                    "summary": {
                        "bar_count": 3,
                        "first_trade_date": "2024-11-27",
                        "last_trade_date": "2024-12-02",
                        "low_close": "230.0000",
                        "high_close": "240.0000",
                        "return_pct": "0.0435",
                    },
                    "price_bars": [
                        {
                            "trade_date": "2024-11-27",
                            "open": "229.0000",
                            "high": "231.0000",
                            "low": "228.0000",
                            "close": "230.0000",
                            "adjusted_close": "230.0000",
                            "volume": 49000000,
                        },
                        {
                            "trade_date": "2024-11-29",
                            "open": "232.0000",
                            "high": "236.0000",
                            "low": "231.0000",
                            "close": "235.0000",
                            "adjusted_close": "235.0000",
                            "volume": 47000000,
                        },
                        {
                            "trade_date": "2024-12-02",
                            "open": "238.0000",
                            "high": "242.0000",
                            "low": "237.0000",
                            "close": "240.0000",
                            "adjusted_close": "240.0000",
                            "volume": 50000000,
                        },
                    ],
                    "recommendation": {
                        "recommendation_id": 7101,
                        "linked_thesis_id": 7001,
                        "action": "monitor_or_accumulate",
                        "score": "0.7800",
                        "status": "active",
                        "as_of_date": "2024-11-01",
                    },
                    "position": {
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "quantity": "10",
                        "weight": "0.0500",
                        "market_price": "223.0000",
                        "market_value": "2230.00",
                        "linked_thesis_id": 7001,
                    },
                    "equity_research": {
                        "artifact_id": 1201,
                        "as_of_date": "2024-12-02",
                        "artifact_type": "full_equity_research",
                        "provider": "fixture",
                        "model_name": "codex-cli-default",
                        "title": "AAPL 기업 리서치 요약",
                        "korean_summary": "애플의 서비스 매출과 현금흐름 품질을 같이 봐야 한다.",
                        "key_points": ["서비스 매출 비중 확대", "현금흐름 품질 양호"],
                        "catalysts": ["신제품 사이클", "서비스 가격 결정력"],
                        "risks": ["중국 수요 둔화"],
                        "invalidation_conditions": ["마진 훼손이 두 분기 지속"],
                        "valuation_sensitivity": {
                            "margin_of_safety": "watch",
                            "upside_case": "서비스 성장 유지",
                        },
                        "source_document_ids": ["aapl-2024-10k-20240928"],
                        "source_run_id": 7711,
                        "created_at": "2024-12-02T09:00:00+00:00",
                    },
                    "industry_competitive_position": {
                        "competitive_position_id": 4101,
                        "as_of_date": "2024-12-02",
                        "methodology": "peer_financial_proxy_v1",
                        "competitive_position": "leader",
                        "peer_group_id": 3101,
                        "peer_group_code": "large_cap_technology",
                        "peer_group_name": "Large Cap Technology",
                        "sector_code": "TECH_DOMAIN",
                        "sector_name": "Technology Domain",
                        "moat_score": "0.8200",
                        "pricing_power_score": "0.7800",
                        "profitability_score": "0.8400",
                        "growth_position_score": "0.7100",
                        "financial_strength_score": "0.9000",
                        "rivalry_risk_score": "0.4200",
                        "buyer_power_risk_score": "0.3800",
                        "supplier_power_risk_score": "0.3300",
                        "substitute_threat_risk_score": "0.2700",
                        "new_entry_threat_risk_score": "0.2400",
                        "capacity_cycle_risk_score": "0.3100",
                        "metric_coverage_count": 9,
                        "peer_count": 8,
                        "key_strengths": ["High profitability percentile", "Strong balance sheet"],
                        "key_risks": ["Large-cap technology rivalry remains material"],
                        "peer_context": {"profitability_percentile": "0.8400"},
                        "rationale": "Peer financial proxy ranks AAPL as a leader.",
                        "source_run_id": 779,
                    },
                    "financial_statement_model": {
                        "statement_scope": "annual",
                        "latest_period_end": "2024-09-28",
                        "latest_as_of_date": "2024-12-02",
                        "latest_fiscal_year": 2024,
                        "latest_fiscal_quarter": None,
                        "period_count": 4,
                        "metric_count": 6,
                        "computed_metric_count": 5,
                        "unavailable_metric_count": 1,
                        "insufficient_history_metric_count": 0,
                        "status_counts": [
                            {"metric_status": "computed", "metric_count": 5},
                            {"metric_status": "unavailable", "metric_count": 1},
                        ],
                        "source_run_ids": [778],
                        "metrics": [
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0610",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                            {
                                "metric_code": "operating_margin",
                                "metric_value": "0.3150",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Operating income divided by revenue.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                            {
                                "metric_code": "free_cash_flow_margin",
                                "metric_value": "0.2470",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Operating cash flow minus capex divided by revenue.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                            {
                                "metric_code": "free_cash_flow_to_net_income",
                                "metric_value": "1.1800",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Free cash flow divided by net income.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                            {
                                "metric_code": "liabilities_to_assets",
                                "metric_value": "0.8200",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Total liabilities divided by total assets.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                            {
                                "metric_code": "roic",
                                "metric_value": None,
                                "metric_unit": "ratio",
                                "metric_status": "unavailable",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Invested capital denominator is missing.",
                                "source_run_id": 778,
                                "created_at": "2024-12-02T10:10:00+00:00",
                            },
                        ],
                        "history": [
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0610",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-12-02",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                            },
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0280",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2023,
                                "fiscal_quarter": None,
                                "period_end": "2023-09-30",
                                "as_of_date": "2024-12-02",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                            },
                        ],
                        "share_count": {
                            "latest_period_end": "2024-09-28",
                            "latest_fiscal_year": 2024,
                            "latest_shares_outstanding": "15300000000",
                            "previous_period_end": "2023-09-30",
                            "previous_shares_outstanding": "15800000000",
                            "share_count_change_pct": "-0.0316",
                            "source_run_id": 778,
                        },
                    },
                    "valuation_methods": [
                        {
                            "valuation_snapshot_id": 5101,
                            "as_of_date": "2024-12-02",
                            "method": "dcf_lite",
                            "base_price": "240.0000",
                            "fair_value_low": "210.0000",
                            "fair_value_base": "270.0000",
                            "fair_value_high": "315.0000",
                            "margin_of_safety": "0.1250",
                            "assumptions": {
                                "model_family": "intrinsic_dcf_lite",
                                "method_description": "Discounted cash flow-lite",
                                "pricing_basis": "latest adjusted close",
                                "price_date": "2024-12-02",
                                "latest_raw_period_end": "2024-09-28",
                                "free_cash_flow": "108807000000",
                                "shares_outstanding": "15300000000",
                                "fcf_per_share": "7.1116",
                                "growth_rate": "0.0280",
                                "discount_rate": "0.1000",
                                "terminal_growth_rate": "0.0250",
                                "forecast_input_source": "market.financial_forecast_input",
                                "latest_forecast_as_of_date": "2024-12-02",
                                "forecast_row_count": 6,
                                "forecast_scenarios": [
                                    {
                                        "scenario_key": "bear",
                                        "forecast_year": 1,
                                        "revenue": "390000000000",
                                        "revenue_growth_rate": "-0.0020",
                                        "free_cash_flow_margin": "0.2400",
                                        "capex_intensity": "0.0400",
                                        "free_cash_flow": "93600000000",
                                        "confidence": "0.4200",
                                    },
                                    {
                                        "scenario_key": "bear",
                                        "forecast_year": 5,
                                        "revenue": "386000000000",
                                        "revenue_growth_rate": "-0.0020",
                                        "free_cash_flow_margin": "0.2400",
                                        "capex_intensity": "0.0400",
                                        "free_cash_flow": "92640000000",
                                        "confidence": "0.4200",
                                    },
                                    {
                                        "scenario_key": "base",
                                        "forecast_year": 1,
                                        "revenue": "402000000000",
                                        "revenue_growth_rate": "0.0280",
                                        "free_cash_flow_margin": "0.2600",
                                        "capex_intensity": "0.0350",
                                        "free_cash_flow": "104520000000",
                                        "confidence": "0.5000",
                                    },
                                    {
                                        "scenario_key": "base",
                                        "forecast_year": 5,
                                        "revenue": "450000000000",
                                        "revenue_growth_rate": "0.0280",
                                        "free_cash_flow_margin": "0.2600",
                                        "capex_intensity": "0.0350",
                                        "free_cash_flow": "117000000000",
                                        "confidence": "0.5000",
                                    },
                                    {
                                        "scenario_key": "bull",
                                        "forecast_year": 1,
                                        "revenue": "414000000000",
                                        "revenue_growth_rate": "0.0580",
                                        "free_cash_flow_margin": "0.2800",
                                        "capex_intensity": "0.0300",
                                        "free_cash_flow": "115920000000",
                                        "confidence": "0.4500",
                                    },
                                    {
                                        "scenario_key": "bull",
                                        "forecast_year": 5,
                                        "revenue": "520000000000",
                                        "revenue_growth_rate": "0.0580",
                                        "free_cash_flow_margin": "0.2800",
                                        "capex_intensity": "0.0300",
                                        "free_cash_flow": "145600000000",
                                        "confidence": "0.4500",
                                    },
                                ],
                                "limitations": [
                                    "5년 FCF/share를 단순 할인한 모델이며 상세 매출·마진·CAPEX forecast를 대체하지 않는다."
                                ],
                            },
                            "confidence": "0.6200",
                            "source_run_id": 7801,
                            "created_at": "2024-12-02T10:00:00+00:00",
                        },
                        {
                            "valuation_snapshot_id": 5102,
                            "as_of_date": "2024-12-02",
                            "method": "relative_multiple",
                            "base_price": "240.0000",
                            "fair_value_low": "220.0000",
                            "fair_value_base": "255.0000",
                            "fair_value_high": "290.0000",
                            "margin_of_safety": "0.0625",
                            "assumptions": {
                                "model_family": "relative_valuation",
                                "method_description": "Peer multiple comparison",
                                "pricing_basis": "latest adjusted close",
                                "price_date": "2024-12-02",
                                "latest_raw_period_end": "2024-09-28",
                                "quality_score": "0.8200",
                                "peer_quality_percentile": "0.7800",
                                "leverage_percentile": "0.3100",
                                "limitations": [
                                    "현재가를 피어 품질 점수로 조정한 상대가치 범위이며 독립적인 내재가치 산정은 아니다."
                                ],
                            },
                            "confidence": "0.5800",
                            "source_run_id": 7801,
                            "created_at": "2024-12-02T10:00:00+00:00",
                        },
                        {
                            "valuation_snapshot_id": 5103,
                            "as_of_date": "2024-12-02",
                            "method": "scenario_range",
                            "base_price": "240.0000",
                            "fair_value_low": "200.0000",
                            "fair_value_base": "260.0000",
                            "fair_value_high": "330.0000",
                            "margin_of_safety": "0.0833",
                            "assumptions": {
                                "model_family": "scenario_range",
                                "method_description": "Bear/base/bull scenario range",
                                "pricing_basis": "latest adjusted close",
                                "price_date": "2024-12-02",
                                "latest_normalized_period_end": "2024-09-28",
                                "quality_score": "0.8200",
                                "normalized_metric_count": 5,
                                "limitations": [
                                    "보수·기준·낙관 case를 가격 앵커와 품질 점수로 만든 단순 범위다."
                                ],
                            },
                            "confidence": "0.6000",
                            "source_run_id": 7801,
                            "created_at": "2024-12-02T10:00:00+00:00",
                        },
                        {
                            "valuation_snapshot_id": 5104,
                            "as_of_date": "2024-12-02",
                            "method": "sum_of_parts",
                            "base_price": "240.0000",
                            "fair_value_low": "198.0000",
                            "fair_value_base": "265.0000",
                            "fair_value_high": "340.0000",
                            "margin_of_safety": "0.1042",
                            "assumptions": {
                                "model_family": "sum_of_parts",
                                "method_description": "Conservative SOTP proxy",
                                "pricing_basis": "latest adjusted close",
                                "price_date": "2024-12-02",
                                "latest_sotp_as_of_date": "2024-12-02",
                                "sotp_component_source": "market.sum_of_parts_component",
                                "sotp_component_count": 3,
                                "segment_footnote_evidence_source": "research.segment_footnote_evidence",
                                "latest_segment_evidence_as_of_date": "2024-12-02",
                                "segment_evidence_count": 3,
                                "reported_segment_metric_count": 4,
                                "segment_data_gap_count": 1,
                                "reported_segment_input_count": 2,
                                "latest_reported_segment_period_end": "2024-09-28",
                                "reported_segment_revenue_total": "485035000000.0000",
                                "reported_segment_operating_income_total": "194500000000.0000",
                                "reported_segment_inputs": [
                                    {
                                        "segment_key": "products",
                                        "segment_label": "Products",
                                        "period_end": "2024-09-28",
                                        "revenue": "391035000000.0000",
                                        "operating_income": "153000000000.0000",
                                        "operating_margin": "0.3913",
                                        "metric_unit": "USD_millions_as_reported",
                                        "source_document_id": 8101,
                                        "confidence": "0.7600",
                                        "source_run_id": 7803,
                                    },
                                    {
                                        "segment_key": "services",
                                        "segment_label": "Services",
                                        "period_end": "2024-09-28",
                                        "revenue": "94000000000.0000",
                                        "operating_income": "41500000000.0000",
                                        "operating_margin": "0.4415",
                                        "metric_unit": "USD_millions_as_reported",
                                        "source_document_id": 8101,
                                        "confidence": "0.7400",
                                        "source_run_id": 7803,
                                    },
                                ],
                                "reported_segment_allocation_count": 2,
                                "reported_segment_allocations": [
                                    {
                                        "segment_key": "products",
                                        "segment_label": "Products",
                                        "period_end": "2024-09-28",
                                        "allocation_basis": "operating_income_share",
                                        "allocation_weight": "0.7866",
                                        "revenue_share": "0.8062",
                                        "operating_income_share": "0.7866",
                                        "allocated_fair_value_low": "165.1860",
                                        "allocated_fair_value_base": "224.1810",
                                        "allocated_fair_value_high": "283.1760",
                                        "revenue": "391035000000.0000",
                                        "operating_income": "153000000000.0000",
                                        "source_document_id": 8101,
                                        "confidence": "0.7600",
                                        "source_run_id": 7803,
                                    },
                                    {
                                        "segment_key": "services",
                                        "segment_label": "Services",
                                        "period_end": "2024-09-28",
                                        "allocation_basis": "operating_income_share",
                                        "allocation_weight": "0.2134",
                                        "revenue_share": "0.1938",
                                        "operating_income_share": "0.2134",
                                        "allocated_fair_value_low": "44.8140",
                                        "allocated_fair_value_base": "60.8190",
                                        "allocated_fair_value_high": "76.8240",
                                        "revenue": "94000000000.0000",
                                        "operating_income": "41500000000.0000",
                                        "source_document_id": 8101,
                                        "confidence": "0.7400",
                                        "source_run_id": 7803,
                                    },
                                ],
                                "reported_segment_assumption_count": 2,
                                "reported_segment_assumptions": [
                                    {
                                        "segment_key": "products",
                                        "segment_label": "Products",
                                        "period_end": "2024-09-28",
                                        "driver_key": "high_margin_cash_engine",
                                        "driver_label": "고마진 현금창출 사업부",
                                        "driver_template_key": "hardware_product_cycle",
                                        "driver_template_label": "제품 교체 사이클·ASP·공급망",
                                        "calibration_method": "multi_period_segment_trend_template",
                                        "history_period_count": 3,
                                        "first_period_end": "2022-09-24",
                                        "latest_period_end": "2024-09-28",
                                        "observed_revenue_cagr": "0.0430",
                                        "observed_margin_change": "0.0180",
                                        "base_growth_rate": "0.0600",
                                        "low_growth_rate": "0.0300",
                                        "high_growth_rate": "0.0900",
                                        "margin_assumption": "0.3913",
                                        "low_multiple": "16.0000",
                                        "base_multiple": "20.0000",
                                        "high_multiple": "24.0000",
                                        "allocation_weight": "0.7866",
                                        "allocation_basis": "operating_income_share",
                                        "rationale": "고마진 현금창출 사업부 · 기준 성장률 6.0% · 기준 multiple 20.0x · operating_income_share",
                                        "source_document_id": 8101,
                                        "confidence": "0.7600",
                                        "source_run_id": 7803,
                                    },
                                    {
                                        "segment_key": "services",
                                        "segment_label": "Services",
                                        "period_end": "2024-09-28",
                                        "driver_key": "high_margin_cash_engine",
                                        "driver_label": "고마진 현금창출 사업부",
                                        "driver_template_key": "services_installed_base",
                                        "driver_template_label": "설치 기반·구독·총마진",
                                        "calibration_method": "multi_period_segment_trend_template",
                                        "history_period_count": 3,
                                        "first_period_end": "2022-09-24",
                                        "latest_period_end": "2024-09-28",
                                        "observed_revenue_cagr": "0.0810",
                                        "observed_margin_change": "0.0240",
                                        "base_growth_rate": "0.0500",
                                        "low_growth_rate": "0.0200",
                                        "high_growth_rate": "0.0800",
                                        "margin_assumption": "0.4415",
                                        "low_multiple": "16.0000",
                                        "base_multiple": "20.0000",
                                        "high_multiple": "24.0000",
                                        "allocation_weight": "0.2134",
                                        "allocation_basis": "operating_income_share",
                                        "rationale": "고마진 현금창출 사업부 · 기준 성장률 5.0% · 기준 multiple 20.0x · operating_income_share",
                                        "source_document_id": 8101,
                                        "confidence": "0.7400",
                                        "source_run_id": 7803,
                                    },
                                ],
                                "has_operating_business_component": True,
                                "sotp_components": [
                                    {
                                        "component_key": "operating_business_fcf",
                                        "component_label": "영업사업 가치",
                                        "component_type": "operating_business",
                                        "fair_value_low": "210.0000",
                                        "fair_value_base": "285.0000",
                                        "fair_value_high": "360.0000",
                                        "valuation_basis": "forecast_or_latest_fcf_multiple",
                                        "assumptions": {
                                            "component_description": "Forecast FCF multiple 기반 핵심 영업사업 가치",
                                        },
                                        "confidence": "0.4500",
                                    },
                                    {
                                        "component_key": "balance_sheet_adjustment",
                                        "component_label": "재무상태 조정",
                                        "component_type": "balance_sheet_adjustment",
                                        "fair_value_low": "8.0000",
                                        "fair_value_base": "15.0000",
                                        "fair_value_high": "25.0000",
                                        "valuation_basis": "book_equity_partial_credit",
                                        "assumptions": {
                                            "component_description": "순자산 일부만 보수적으로 반영",
                                        },
                                        "confidence": "0.3500",
                                    },
                                    {
                                        "component_key": "segment_data_gap_reserve",
                                        "component_label": "세그먼트 데이터 공백 차감",
                                        "component_type": "risk_reserve",
                                        "fair_value_low": "-20.0000",
                                        "fair_value_base": "-35.0000",
                                        "fair_value_high": "-45.0000",
                                        "valuation_basis": "segment_data_gap_reserve",
                                        "assumptions": {
                                            "component_description": "세그먼트 데이터 부족을 반영한 reserve",
                                            "segment_evidence": [
                                                {
                                                    "segment_key": "filing_anchor",
                                                    "segment_label": "SEC 공시 원천 문서",
                                                    "evidence_type": "filing_anchor",
                                                    "metric_code": "source_document",
                                                    "metric_value": None,
                                                    "metric_unit": "n/a",
                                                    "period_end": "2024-09-28",
                                                    "source_document_id": 8101,
                                                    "evidence_text": "10-K - Apple annual report",
                                                    "confidence": "0.7000",
                                                    "source_run_id": 7803,
                                                },
                                                {
                                                    "segment_key": "consolidated_total",
                                                    "segment_label": "연결 기준 전체 회사",
                                                    "evidence_type": "consolidated_metric",
                                                    "metric_code": "revenue",
                                                    "metric_value": "391035000000.0000",
                                                    "metric_unit": "USD",
                                                    "period_end": "2024-09-28",
                                                    "source_document_id": 8101,
                                                    "evidence_text": "AAPL consolidated revenue from SEC companyfacts",
                                                    "confidence": "0.6500",
                                                    "source_run_id": 7803,
                                                },
                                                {
                                                    "segment_key": "segment_data_gap",
                                                    "segment_label": "사업부별 세그먼트 데이터 공백",
                                                    "evidence_type": "segment_data_gap",
                                                    "metric_code": "segment_detail",
                                                    "metric_value": None,
                                                    "metric_unit": "n/a",
                                                    "period_end": "2024-09-28",
                                                    "source_document_id": 8101,
                                                    "evidence_text": "SEC footnote parser has not confirmed reported business segment metrics for AAPL",
                                                    "confidence": "0.8000",
                                                    "source_run_id": 7803,
                                                },
                                            ],
                                        },
                                        "confidence": "0.5000",
                                    },
                                ],
                                "limitations": [
                                    "첫 SOTP foundation은 사업부별 segment forecast가 아니라 FCF와 재무상태 기반 proxy component다."
                                ],
                            },
                            "confidence": "0.5000",
                            "source_run_id": 7802,
                            "created_at": "2024-12-02T10:00:00+00:00",
                        },
                    ],
                    "macro_flow_impacts": [
                        {
                            "event_id": 9101,
                            "title": "Fed signals higher for longer",
                            "event_type": "rss_news_event",
                            "event_at": "2024-12-01T12:00:00+00:00",
                            "theme_key": "MACRO_RATES_FED",
                            "theme_name": "Fed and rates",
                            "impact_direction": "risk_review",
                            "impact_score": "0.5200",
                            "confidence": "0.7500",
                            "exposure_weight": "0.6500",
                            "rationale": "MACRO_RATES_FED flow propagated to AAPL",
                            "source_document_id": "fed-rates-20241201",
                            "ai_evidence_id": 8802,
                            "source_run_id": 7701,
                        }
                    ],
                    "recent_events": [
                        {
                            "event_id": 9001,
                            "title": "AAPL 2024 10-K annual reporting event",
                            "korean_title": "애플 2024년 10-K 연차 보고 이벤트",
                            "korean_summary": "애플 연차 보고서가 장기 투자 논리 점검 근거로 연결됐다.",
                            "translation_confidence": "0.9100",
                            "event_type": "source_document_event",
                            "event_at": "2024-09-28T00:00:00+00:00",
                            "impact_direction": "supportive",
                            "impact_score": "0.8200",
                            "source_document_id": "aapl-2024-10k-20240928",
                            "ai_evidence_id": 8801,
                        }
                    ],
                }
            )
        if sql.startswith("-- ai evidence neighborhood lookup"):
            return json.dumps(
                {
                    "query": {"primary_symbol": "AAPL", "as_of_date": "2024-12-02", "limit": 25},
                    "instrument": {
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "name": "Apple Inc.",
                        "market_code": "US",
                    },
                    "themes": [
                        {
                            "node_id": 701,
                            "taxonomy_family": "internal_theme",
                            "node_type": "theme",
                            "code": "ANNUAL_REPORTING",
                            "name": "Annual Reporting",
                            "membership_type": "seeded",
                            "confidence": "0.9000",
                            "source_document_id": 301,
                        }
                    ],
                    "theme_edges": [
                        {
                            "edge_id": 41,
                            "parent_code": "QUALITY_COMPOUNDERS",
                            "child_code": "ANNUAL_REPORTING",
                            "relation_type": "contains",
                            "weight": "0.8000",
                        }
                    ],
                    "events": [
                        {
                            "event_id": 9001,
                            "title": "AAPL 2024 10-K annual reporting event",
                            "korean_title": "애플 2024년 10-K 연차 보고 이벤트",
                            "korean_summary": "애플 연차 보고서가 장기 투자 논리 점검 근거로 연결됐다.",
                            "translation_confidence": "0.9100",
                            "event_type": "source_document_event",
                            "event_at": "2024-09-28T00:00:00+00:00",
                            "instrument_impact_direction": "supportive",
                            "instrument_impact_strength": "0.8200",
                            "theme_impact_direction": "supportive",
                            "theme_impact_strength": "0.7500",
                            "theme_key": "ANNUAL_REPORTING",
                            "document_id": 301,
                            "external_document_id": "aapl-2024-10k-20240928",
                        }
                    ],
                    "ai_artifacts": [
                        {
                            "artifact_id": 8801,
                            "event_id": 9001,
                            "document_id": 301,
                            "artifact_type": "source_document_event",
                            "confidence": "0.8600",
                            "provider": "openai",
                            "model_name": "responses-frontier-placeholder",
                            "status": "succeeded",
                            "estimated_cost_usd": "0.0184",
                        }
                    ],
                    "evidence_chunks": [
                        {
                            "chunk_id": 30001,
                            "document_id": 301,
                            "chunk_index": 0,
                            "text_preview": "Company overview and segment framing.",
                            "token_count": 128,
                            "chunk_metadata": {
                                "source_text_kind": "raw_html_text",
                                "used_metadata_fallback": False,
                            },
                            "source_url": "https://www.sec.gov/Archives/edgar/data/320193/aapl-2024-10k.htm",
                            "embedding_id": 9901,
                            "embedding_provider": "local",
                            "embedding_model_name": "deterministic-test",
                            "vector_storage_uri": "secret://do-not-expose",
                        }
                    ],
                    "theses": [
                        {
                            "thesis_id": 7001,
                            "title": "AAPL long-term compounder thesis",
                            "status": "active",
                            "conviction_score": "0.7400",
                            "expected_holding_days": 730,
                            "invalidation_conditions": "Services margin deterioration.",
                        }
                    ],
                    "recommendations": [
                        {
                            "recommendation_id": 7101,
                            "as_of_date": "2024-11-01",
                            "action": "monitor_or_accumulate",
                            "bucket": "core",
                            "total_score": "0.7800",
                            "recommended_weight": "0.0600",
                            "thesis_id": 7001,
                        }
                    ],
                    "positions": [
                        {
                            "portfolio_name": "Long Term Paper",
                            "snapshot_date": "2024-11-01",
                            "market_value": "2230.00",
                            "weight": "0.0500",
                            "linked_thesis_id": 7001,
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend paper trading preview state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-12-02",
                    "portfolio_name": "Long Term Paper",
                    "strategy_name": "long_term_core",
                    "latest_recommendation_batch": {
                        "as_of_date": "2024-12-02",
                        "horizon_type": "long_term",
                        "universe_version": "bootstrap-v1",
                    },
                    "quality_summary": {
                        "recommendation_count": 2,
                        "measured_recommendation_count": 1,
                        "unmeasured_recommendation_count": 1,
                        "hit_rate": "1.0000",
                        "average_alpha": "0.0600",
                        "position_recommendation_conflict_count": 1,
                        "paper_action_count": 2,
                        "requires_human_approval_count": 2,
                    },
                    "guardrails": [
                        "이 화면은 가상 거래 미리보기이며 실제 주문을 만들지 않는다.",
                        "모든 가상 조치는 거래 안전 승인 전까지 실행되지 않는다.",
                        "실거래 증권사 API, 계좌 권한, 주문 전송은 아직 연결하지 않았다.",
                    ],
                    "paper_actions": [
                        {
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "recommendation_id": 7101,
                            "linked_thesis_id": 7001,
                            "recommendation_action": "exclude",
                            "recommendation_score": "0.2579",
                            "recommendation_as_of_date": "2024-12-02",
                            "latest_price_date": "2024-12-02",
                            "latest_price": "240.0000",
                            "current_weight": "0.0500",
                            "target_weight": "0.0000",
                            "paper_action": "paper_sell_to_zero",
                            "reason": "추천은 제외/매도인데 현재 보유 중이다. 실제 주문 없이 가상 매도 후보로 표시한다.",
                            "risk_level": "high",
                            "requires_human_approval": True,
                            "conflict": True,
                        },
                        {
                            "symbol": "MSFT",
                            "instrument_id": 503,
                            "recommendation_id": 7102,
                            "linked_thesis_id": 7002,
                            "recommendation_action": "monitor_or_accumulate",
                            "recommendation_score": "0.7300",
                            "recommendation_as_of_date": "2024-12-02",
                            "latest_price_date": "2024-12-02",
                            "latest_price": "426.8000",
                            "current_weight": "0.0000",
                            "target_weight": "0.0300",
                            "paper_action": "paper_buy_to_target",
                            "reason": "추천 목표 비중이 있고 현재 미보유다. 실제 주문 없이 가상 매수 후보로 표시한다.",
                            "risk_level": "medium",
                            "requires_human_approval": True,
                            "conflict": False,
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend trading readiness state lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "execution_mode": "paper",
                    "broker_boundary": {
                        "broker_code": "simulated_paper",
                        "environment": "paper",
                        "status": "enabled",
                        "supports_order_preview": True,
                        "supports_order_submit": False,
                        "secret_configured": False,
                        "notes": "paper-only simulated broker",
                        "updated_at": "2026-05-19T00:00:00+00:00",
                    },
                    "account_permission": {
                        "account_ref": "paper-account-1",
                        "permission_scope": "paper_trade",
                        "status": "active",
                        "allowed_symbol_count": 2,
                        "allows_all_symbols": False,
                        "max_order_notional": "50000.00",
                        "max_daily_notional": "100000.00",
                        "approved_by": "operator",
                        "approved_at": "2026-05-19T00:00:00+00:00",
                        "updated_at": "2026-05-19T00:00:00+00:00",
                    },
                    "order_limit_policy": {
                        "policy_name": "long-term-paper-default",
                        "status": "active",
                        "max_single_order_notional": "50000.00",
                        "max_daily_order_notional": "100000.00",
                        "max_single_order_weight_delta": "0.2000",
                        "max_post_trade_symbol_weight": "0.4000",
                        "min_cash_buffer_weight": "0.0200",
                        "updated_at": "2026-05-19T00:00:00+00:00",
                    },
                    "kill_switches": [
                        {
                            "scope": "global",
                            "scope_ref": "global",
                            "is_engaged": True,
                            "reason": "default locked until explicit operator approval",
                            "changed_by": "migration-0013",
                            "changed_at": "2026-05-19T00:00:00+00:00",
                        }
                    ],
                    "paper_validation": {
                        "validation_date": "2026-05-19",
                        "status": "failed",
                        "recommendation_count": 2,
                        "conflict_count": 1,
                        "approved_action_count": 1,
                        "validated_symbol_count": 1,
                        "blocked_reasons": ["position_recommendation_conflict:AAPL"],
                        "created_by": "paper-validation-smoke",
                        "created_at": "2026-05-19T00:00:00+00:00",
                    },
                    "portfolio_risk_budget_guardrail": {
                        "status": "loaded",
                        "eval_run_id": 23,
                        "as_of_date": "2026-05-25",
                        "effective_snapshot_date": "2026-05-25",
                        "risk_gate_decision": "blocked_by_risk_budget_review",
                        "paper_validation_input_allowed": False,
                        "blocking_reasons": [
                            {"code": "over_single_position_limit"},
                            {"code": "sector_over_limit"},
                        ],
                        "warning_reasons": [{"code": "insufficient_benchmark_composition"}],
                        "benchmark_drift": {
                            "status": "calculated",
                            "benchmark_code": "SPY",
                            "benchmark_source": "ssga_spdr_spy_daily_holdings",
                            "source_type": "provider_file",
                            "source_as_of_date": "2026-05-21",
                            "drift_calculated": True,
                            "component_count": 503,
                            "composition_coverage_weight": "0.99837820",
                            "active_share": "0.77853213",
                            "total_absolute_drift": "1.55706426",
                            "top_active_positions": [
                                {
                                    "symbol": "TSLA",
                                    "portfolio_weight": "0.30680000",
                                    "benchmark_weight": "0.01839095",
                                    "active_weight": "0.28840905",
                                },
                                {
                                    "symbol": "MSFT",
                                    "portfolio_weight": "0.30780000",
                                    "benchmark_weight": "0.04870486",
                                    "active_weight": "0.25909514",
                                },
                                {
                                    "symbol": "AAPL",
                                    "portfolio_weight": "0.22710000",
                                    "benchmark_weight": "0.07007801",
                                    "active_weight": "0.15702199",
                                },
                                {
                                    "symbol": "AMZN",
                                    "portfolio_weight": "0",
                                    "benchmark_weight": "0.04104394",
                                    "active_weight": "-0.04104394",
                                },
                            ],
                        },
                    },
                    "audit_summary": {
                        "intent_count": 3,
                        "blocked_count": 2,
                        "approved_for_paper_count": 1,
                        "approved_for_live_count": 0,
                        "submitted_to_broker_count": 0,
                        "latest_created_at": "2026-05-19T00:10:00+00:00",
                    },
                }
            )
        if sql.startswith("-- frontend cycle state list lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-11-01",
                    "strategy_name": "long_term_core",
                    "horizon_type": "long_term",
                    "universe_version": "bootstrap-v1",
                    "cycle_states": [
                        {
                            "theme_key": "ANNUAL_REPORTING",
                            "theme_name": "Annual reporting quality",
                            "state": "constructive",
                            "previous_state": "neutral",
                            "confidence": "0.7200",
                            "instrument_count": 1,
                            "top_symbols": ["AAPL"],
                            "features": {
                                "event_intensity": "0.8000",
                                "price_momentum": "0.6100",
                                "fundamental_quality": "0.7400",
                            },
                        },
                        {
                            "theme_key": "CHINA_ADR_COVERAGE",
                            "theme_name": "China ADR coverage",
                            "state": "incomplete_coverage",
                            "previous_state": "unknown",
                            "confidence": "0.4100",
                            "instrument_count": 1,
                            "top_symbols": ["BABA"],
                            "features": {
                                "event_intensity": "0.2000",
                                "price_momentum": "0.4800",
                                "fundamental_quality": None,
                            },
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend portfolio risk budget guardrail lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 23,
                    "as_of_date": "2026-05-25",
                    "effective_snapshot_date": "2026-05-25",
                    "risk_gate_decision": "blocked_by_risk_budget_review",
                    "paper_validation_input_allowed": False,
                    "blocking_reasons": [{"code": "over_single_position_limit"}],
                    "warning_reasons": [],
                    "benchmark_drift": {
                        "status": "calculated",
                        "benchmark_code": "SPY",
                        "benchmark_source": "ssga_spdr_spy_daily_holdings",
                        "source_type": "provider_file",
                        "source_as_of_date": "2026-05-21",
                        "drift_calculated": True,
                        "component_count": 503,
                        "composition_coverage_weight": "0.99837820",
                        "active_share": "0.77853213",
                        "total_absolute_drift": "1.55706426",
                        "top_active_positions": [
                            {
                                "symbol": "TSLA",
                                "portfolio_weight": "0.30680000",
                                "benchmark_weight": "0.01839095",
                                "active_weight": "0.28840905",
                            },
                            {
                                "symbol": "MSFT",
                                "portfolio_weight": "0.30780000",
                                "benchmark_weight": "0.04870486",
                                "active_weight": "0.25909514",
                            },
                        ],
                    },
                }
            )
        if sql.startswith("-- frontend portfolio review decision history lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 52,
                    "created_at": "2026-05-27T02:00:00+00:00",
                    "eval_name": "portfolio_review_decision_history",
                    "dataset_version": "portfolio-review-decision-history-v1",
                    "as_of_date": "2026-05-25",
                    "portfolio_name": "Long Term Paper",
                    "source_portfolio_coverage_as_of_date": "2026-05-25",
                    "coverage_measurement_end_date": "2026-06-25",
                    "decision_status": "review_required",
                    "decision_count": 2,
                    "review_required_count": 2,
                    "benchmark_decision_count": 1,
                    "position_sizing_decision_count": 1,
                    "decision_counts": {"reduce_watch": 1, "add_blocked_until_evidence": 1},
                    "top_decision": {
                        "decision_family": "benchmark_drift",
                        "symbol": "TSLA",
                        "priority": 1,
                        "decision_type": "reduce_watch",
                        "decision_label": "비중 축소 검토",
                        "next_review_action": "추가 매수를 막고 축소 여부만 검토한다.",
                        "severity": "high",
                        "current_weight": "0.3068",
                        "benchmark_weight": "0.01839095",
                        "active_weight": "0.28840905",
                        "source_evidence": {"benchmark_code": "SPY"},
                        "links": {"stock": "/stocks/TSLA"},
                        "decision_path": [],
                        "rationale": "TSLA active weight가 크다.",
                        "review_required": True,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "latest_decisions": [
                        {
                            "decision_family": "benchmark_drift",
                            "symbol": "TSLA",
                            "priority": 1,
                            "decision_type": "reduce_watch",
                            "decision_label": "비중 축소 검토",
                            "next_review_action": "추가 매수를 막고 축소 여부만 검토한다.",
                            "severity": "high",
                            "current_weight": "0.3068",
                            "benchmark_weight": "0.01839095",
                            "active_weight": "0.28840905",
                            "source_evidence": {"benchmark_code": "SPY"},
                            "links": {"stock": "/stocks/TSLA"},
                            "decision_path": [],
                            "rationale": "TSLA active weight가 크다.",
                            "review_required": True,
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        }
                    ],
                    "guardrails": {
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "next_action": "최신 포트폴리오 검토 결정을 확인한다.",
                }
            )
        if sql.startswith("-- frontend portfolio review decision outcome feedback lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 53,
                    "created_at": "2026-05-27T03:00:00+00:00",
                    "eval_name": "portfolio_review_decision_outcome_feedback",
                    "dataset_version": "portfolio-review-decision-outcome-feedback-v1",
                    "as_of_date": "2026-05-27",
                    "portfolio_name": "Long Term Paper",
                    "source_history_eval_run_id": 52,
                    "source_history_as_of_date": "2026-05-25",
                    "min_horizon_days": 30,
                    "history_age_days": 2,
                    "feedback_status": "too_early",
                    "decision_count": 1,
                    "too_early_count": 1,
                    "validated_count": 0,
                    "contradicted_count": 0,
                    "needs_more_data_count": 0,
                    "status_counts": {"too_early": 1},
                    "paper_validation": {"status": "missing", "conflict_count": 0},
                    "top_feedback": {
                        "decision_index": 1,
                        "decision_family": "benchmark_drift",
                        "symbol": "TSLA",
                        "decision_type": "reduce_watch",
                        "decision_label": "비중 축소 검토",
                        "feedback_status": "too_early",
                        "feedback_reason": "30일 최소 관찰 기간이 아직 끝나지 않았다.",
                        "source_decision": {
                            "priority": 1,
                            "severity": "high",
                            "current_weight": "0.3068",
                            "benchmark_weight": "0.01839095",
                            "active_weight": "0.28840905",
                            "related_recommendation_id": "recommendation-61",
                            "related_thesis_id": "thesis-1",
                            "rationale": "TSLA active weight가 크다.",
                        },
                        "evidence": {
                            "recommendation_outcome": {},
                            "thesis": {"status": "active"},
                            "thesis_outcome": {},
                            "price_evidence": {},
                            "paper_validation": {"status": "missing", "conflict_count": 0},
                        },
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "latest_items": [
                        {
                            "decision_index": 1,
                            "decision_family": "benchmark_drift",
                            "symbol": "TSLA",
                            "decision_type": "reduce_watch",
                            "decision_label": "비중 축소 검토",
                            "feedback_status": "too_early",
                            "feedback_reason": "30일 최소 관찰 기간이 아직 끝나지 않았다.",
                            "source_decision": {
                                "priority": 1,
                                "severity": "high",
                                "current_weight": "0.3068",
                                "benchmark_weight": "0.01839095",
                                "active_weight": "0.28840905",
                                "related_recommendation_id": "recommendation-61",
                                "related_thesis_id": "thesis-1",
                                "rationale": "TSLA active weight가 크다.",
                            },
                            "evidence": {
                                "recommendation_outcome": {},
                                "thesis": {"status": "active"},
                                "thesis_outcome": {},
                                "price_evidence": {},
                                "paper_validation": {"status": "missing", "conflict_count": 0},
                            },
                            "automatic_order_allowed": False,
                            "broker_submit_allowed": False,
                            "order_boundary": "read_only_no_order",
                        }
                    ],
                    "guardrails": {
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "next_action": "성과 측정 window가 끝날 때까지 기다린다.",
                }
            )
        if sql.startswith("-- frontend portfolio position sizing context lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2024-11-01",
                    "positions": [
                        {
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "weight": "0.0500",
                            "linked_thesis_id": 7001,
                            "recommendation_id": 7101,
                            "recommendation_action": "monitor_or_accumulate",
                            "recommendation_score": "0.7300",
                            "recommended_weight": "0.0500",
                            "recommendation_as_of_date": "2024-11-01",
                            "components": {
                                "fundamental_quality_score": "0.6750",
                                "valuation_margin_score": "0.3990",
                                "peer_relative_score": "0.6100",
                                "balance_sheet_risk_penalty": "0.7200",
                                "thesis_consistency_score": "0.8000",
                            },
                            "valuation": {
                                "as_of_date": "2024-11-01",
                                "method_count": 3,
                                "margin_of_safety": "0.1250",
                                "confidence": "0.6800",
                                "methods": [],
                            },
                            "equity_research": {
                                "artifact_id": 1201,
                                "as_of_date": "2024-11-01",
                                "provider": "codex_oauth",
                                "model_name": "codex-oauth",
                                "title": "AAPL full research",
                                "korean_summary": "AAPL은 재무 품질과 현금흐름이 안정적이다.",
                            },
                        },
                        {
                            "symbol": "BABA",
                            "instrument_id": 502,
                            "weight": "0.0300",
                            "linked_thesis_id": None,
                            "components": {
                                "fundamental_quality_score": None,
                                "valuation_margin_score": None,
                                "peer_relative_score": None,
                                "balance_sheet_risk_penalty": None,
                                "thesis_consistency_score": None,
                            },
                            "valuation": {
                                "method_count": 0,
                                "methods": [],
                            },
                            "equity_research": {},
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend cycle map state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-11-01",
                    "summary": {
                        "node_count": 3,
                        "macro_count": 1,
                        "domain_count": 1,
                        "sector_count": 0,
                        "theme_count": 1,
                        "instrument_count": 0,
                        "conflict_node_count": 1,
                        "direct_event_count": 4,
                        "propagated_impact_count": 6,
                        "recommendation_count": 2,
                        "thesis_count": 1,
                        "hot_node_code": "MACRO_RATES_FED",
                    },
                    "nodes": [
                        {
                            "node_id": 101,
                            "node_code": "MACRO_RATES_FED",
                            "node_name": "Macro Rates and Fed",
                            "node_type": "macro_regime",
                            "description": "Rates, inflation, and Fed policy path.",
                            "cycle_level": "macro",
                            "cycle_state": "forming",
                            "cycle_score": "0.6200",
                            "trend_score": "0.5800",
                            "breadth_score": "0.5200",
                            "event_heat_score": "0.8100",
                            "liquidity_score": "0.4900",
                            "valuation_pressure": "0.5700",
                            "parent_alignment_score": "0.7100",
                            "conflict_flags": ["growth_vs_rates"],
                            "evidence_event_ids": [9001, 9002],
                            "summary_text_ko": "금리·연준 흐름은 직접 뉴스 2건과 전파 영향 3건이 있다.",
                            "top_symbols": ["SPY", "QQQ", "TLT"],
                            "recent_event_titles": ["Fed rates remain in focus"],
                            "parent_codes": [],
                            "child_codes": ["TECH_DOMAIN"],
                            "counts": {
                                "parent_edge_count": 0,
                                "child_edge_count": 1,
                                "direct_event_count": 2,
                                "propagated_impact_count": 3,
                                "exposed_instrument_count": 3,
                                "ai_artifact_count": 1,
                                "recommendation_count": 1,
                                "thesis_count": 1,
                            },
                            "summary_as_of_date": "2024-11-01",
                            "source_run_id": 9201,
                            "updated_at": "2024-11-01T12:00:00+00:00",
                        },
                        {
                            "node_id": 201,
                            "node_code": "TECH_DOMAIN",
                            "node_name": "Technology Domain",
                            "node_type": "domain",
                            "description": "Technology and AI infrastructure.",
                            "cycle_level": "domain",
                            "cycle_state": "expanding",
                            "cycle_score": "0.7400",
                            "event_heat_score": "0.6400",
                            "conflict_flags": [],
                            "evidence_event_ids": [],
                            "summary_text_ko": "기술 도메인은 AI 인프라 수요와 연결된다.",
                            "top_symbols": ["NVDA"],
                            "recent_event_titles": [],
                            "parent_codes": ["MACRO_RATES_FED"],
                            "child_codes": ["AI_SEMICONDUCTOR_CYCLE"],
                            "counts": {
                                "parent_edge_count": 1,
                                "child_edge_count": 1,
                                "direct_event_count": 1,
                                "propagated_impact_count": 2,
                                "exposed_instrument_count": 1,
                                "ai_artifact_count": 1,
                                "recommendation_count": 1,
                                "thesis_count": 0,
                            },
                            "summary_as_of_date": "2024-11-01",
                            "source_run_id": 9201,
                            "updated_at": "2024-11-01T12:00:00+00:00",
                        },
                    ],
                    "edges": [
                        {
                            "parent_code": "MACRO_RATES_FED",
                            "parent_name": "Macro Rates and Fed",
                            "child_code": "TECH_DOMAIN",
                            "child_name": "Technology Domain",
                            "relation_type": "macro_to_domain",
                            "weight": "0.7500",
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend market map state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2026-06-05",
                    "snapshot_as_of_date": "2026-06-05",
                    "summary": {
                        "status": "partial_or_stale",
                        "indicator_count": 3,
                        "fresh_indicator_count": 2,
                        "stale_indicator_count": 1,
                        "missing_indicator_count": 0,
                        "shock_indicator_count": 2,
                        "regime_count": 2,
                        "active_regime_count": 1,
                        "watch_regime_count": 1,
                        "conflict_regime_count": 0,
                        "news_link_count": 1,
                        "latest_observation_date": "2026-06-05",
                        "next_action": "stale 지표는 추정값으로 채우지 말고 provider fetch와 snapshot을 다시 실행한다.",
                    },
                    "groups": [
                        {
                            "group_code": "dollar",
                            "group_name": "달러",
                            "indicator_count": 1,
                            "fresh_count": 0,
                            "stale_count": 1,
                            "missing_count": 0,
                            "shock_count": 0,
                            "latest_observation_date": "2026-05-29",
                            "strongest_indicator_code": "USD_BROAD_INDEX",
                            "indicators": [
                                {
                                    "indicator_code": "USD_BROAD_INDEX",
                                    "display_name": "미국 달러 광의 지수",
                                    "indicator_type": "dollar",
                                    "preferred_provider": "fred",
                                    "fallback_provider": None,
                                    "provider_symbol": "DTWEXBGS",
                                    "latest_observation_date": "2026-05-29",
                                    "latest_value": "123.4500",
                                    "return_20d": None,
                                    "trend_state": "stale",
                                    "shock_direction": "neutral",
                                    "shock_magnitude": "0.0000",
                                    "confidence": "0.3500",
                                    "freshness_status": "stale",
                                    "stale_policy": "mark_stale_no_imputation_weaken_dollar_regime",
                                    "quality_policy": "stale_dollar_index_weakens_dollar_regime_confidence",
                                    "quality_note_ko": "FRED 달러 광의 지수가 오래되어 달러 유동성 판단 신뢰도를 낮춘다. 추정값으로 채우지 않는다.",
                                    "note_ko": "달러 지표가 오래되어 달러 유동성 판단은 약하게 본다.",
                                    "source_policy": {
                                        "license_note": "FRED public API.",
                                        "redistribution_allowed_note": "Show normalized indicators only.",
                                        "causal_claim": False,
                                    },
                                }
                            ],
                        }
                    ],
                    "regimes": [
                        {
                            "regime_code": "dollar_liquidity_tightening",
                            "regime_state": "watch",
                            "regime_score": "0.4200",
                            "confidence": "0.3500",
                            "driver_indicator_codes": ["USD_BROAD_INDEX"],
                            "conflict_flags": [],
                            "summary_ko": "달러 강세와 유동성 긴축 압력이 있는지 본다.",
                        }
                    ],
                    "news_links": [
                        {
                            "document_id": 501,
                            "event_id": 601,
                            "indicator_code": "USD_BROAD_INDEX",
                            "indicator_name": "미국 달러 광의 지수",
                            "link_date": "2026-06-05",
                            "relationship": "news_with_indicator_shock",
                            "confidence": "0.5000",
                            "rationale": "인과 확정이 아니라 시간상 근거 후보이다.",
                            "title_ko": "달러와 금리 흐름 관련 뉴스",
                            "source_name": "fixture",
                            "source_url": "https://example.com/news",
                        }
                    ],
                    "quality_flags": [
                        {
                            "flag_code": "stale_fred_dollar_index",
                            "severity": "medium",
                            "indicator_code": "USD_BROAD_INDEX",
                            "display_name": "미국 달러 광의 지수",
                            "freshness_status": "stale",
                            "stale_policy": "mark_stale_no_imputation_weaken_dollar_regime",
                            "latest_observation_date": "2026-05-29",
                            "message_ko": "FRED 달러 광의 지수가 stale이다. 달러 강세/약세 regime 판단은 약하게 보며 추정값으로 채우지 않는다.",
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend event list state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-11-01",
                    "summary": {
                        "event_count": 1,
                        "ai_extracted_count": 1,
                        "news_event_candidate_count": 1,
                        "news_cluster_summary_count": 0,
                        "unreviewed_event_count": 0,
                        "source_document_count": 1,
                        "themes_represented": 1,
                    },
                    "events": [
                        {
                            "event_id": 9001,
                            "title": "AAPL 2024 10-K annual reporting event",
                            "event_type": "source_document_event",
                            "event_at": "2024-09-28T00:00:00+00:00",
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "theme_key": "ANNUAL_REPORTING",
                            "theme_name": "Annual reporting quality",
                            "impact_direction": "supportive",
                            "impact_score": "0.8200",
                            "source_document_id": "aapl-2024-10k-20240928",
                            "ai_evidence_id": 8801,
                            "ai_evidence_type": "source_document_event",
                            "ai_evidence_provider": "openai",
                            "ai_evidence_confidence": "0.8600",
                            "quality_gate": "ai_review_passed",
                            "related_events": [
                                {
                                    "event_id": 9002,
                                    "title": "AAPL annual report risk factor follow-up",
                                    "relation_type": "same_source_document",
                                    "relation_strength": "0.9500",
                                    "reason": "같은 원천 문서에서 파생된 이벤트다.",
                                    "symbol": "AAPL",
                                    "theme_key": "ANNUAL_REPORTING",
                                    "event_at": "2024-09-28T00:00:00+00:00",
                                }
                            ],
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend theme detail state lookup"):
            return json.dumps(
                {
                    "theme_key": "ANNUAL_REPORTING",
                    "theme_name": "Annual reporting quality",
                    "as_of_date": "2024-11-01",
                    "state": "constructive",
                    "previous_state": "neutral",
                    "confidence": "0.7200",
                    "cycle_score": "0.7400",
                    "cycle_history": [
                        {"as_of_date": "2024-10-01", "state": "neutral", "confidence": "0.5800"},
                        {"as_of_date": "2024-11-01", "state": "constructive", "confidence": "0.7200"},
                    ],
                    "features": {
                        "event_intensity": "0.8000",
                        "price_momentum": "0.6100",
                        "fundamental_quality": "0.7400",
                    },
                    "linked_instruments": [
                        {
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "membership_strength": "0.8600",
                            "active_thesis_id": 7001,
                            "latest_recommendation_id": 7101,
                        }
                    ],
                    "supporting_events": [
                        {
                            "event_id": 9001,
                            "title": "AAPL 2024 10-K annual reporting event",
                            "event_at": "2024-09-28T00:00:00+00:00",
                            "symbol": "AAPL",
                            "impact_direction": "supportive",
                            "impact_score": "0.8200",
                            "ai_evidence_id": 8801,
                            "source_document_id": "aapl-2024-10k-20240928",
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend performance outcomes state lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "strategy_name": "long_term_core",
                    "snapshot_date": "2024-11-01",
                    "measurement_start_date": "2024-11-01",
                    "measurement_end_date": "2024-12-02",
                    "benchmark_code": "SPY",
                    "methodology": "position_weighted_alpha_v1",
                    "summary": {
                        "measured_recommendation_count": 1,
                        "measured_thesis_count": 1,
                        "outperform_count": 1,
                        "underperform_count": 0,
                        "hit_rate": "1.0000",
                        "average_alpha": "0.0600",
                        "security_lens_contribution_bps": "30.0000",
                        "theme_lens_contribution_bps": "30.0000",
                        "cash_timing_contribution_bps": "0.0000",
                        "attribution_component_count": 3,
                        "excluded_position_count": 1,
                        "excluded_weight": "0.0300",
                        "cash_weight": "0.9200",
                    },
                    "quality_evaluation": {
                        "status": "insufficient_sample",
                        "sample_size_status": "insufficient_sample",
                        "score_outcome_alignment": "insufficient_sample",
                        "review_outcome_mismatch_count": 0,
                        "measured_recommendation_count": 1,
                        "measured_thesis_count": 1,
                        "average_alpha": "0.0600",
                        "hit_rate": "1.0000",
                        "high_score_recommendation_count": 1,
                        "high_score_average_alpha": "0.0600",
                        "coverage_exclusion_count": 1,
                    },
                    "outcomes": [
                        {
                            "outcome_id": 8101,
                            "recommendation_id": 7101,
                            "thesis_id": 7001,
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "recommendation": "accumulate",
                            "horizon_days": 31,
                            "absolute_return": "0.1000",
                            "benchmark_return": "0.0400",
                            "alpha": "0.0600",
                            "label": "outperform",
                            "position_weight": "0.0500",
                            "security_contribution_bps": "30.0000",
                            "source_run_id": 9102,
                        }
                    ],
                    "attribution_components": [
                        {
                            "component_id": 8201,
                            "component_type": "security_selection",
                            "label": "AAPL security selection",
                            "symbol": "AAPL",
                            "theme_key": "ANNUAL_REPORTING",
                            "weight": "0.0500",
                            "absolute_return": "0.1000",
                            "benchmark_return": "0.0400",
                            "alpha": "0.0600",
                            "contribution_bps": "30.0000",
                            "interpretation": "Position-weighted alpha contribution.",
                        }
                    ],
                    "coverage_exclusions": [
                        {
                            "symbol": "BABA",
                            "instrument_id": 502,
                            "weight": "0.0300",
                            "reason": "missing_thesis",
                            "required_action": "needs_thesis_review",
                        }
                    ],
                    "quality_gates": [
                        {
                            "gate": "coverage_ready",
                            "status": "blocked",
                            "reason": "Some positions are excluded from attribution coverage.",
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend recommendation detail state lookup"):
            return json.dumps(
                {
                    "recommendation_id": 7101,
                    "symbol": "AAPL",
                    "instrument_id": 501,
                    "as_of_date": "2024-11-01",
                    "strategy_name": "long_term_core",
                    "horizon_type": "long_term",
                    "recommendation": "monitor_or_accumulate",
                    "score": "0.7800",
                    "score_version": "bootstrap-v1",
                    "score_components": [
                        {
                            "component": "cycle_score",
                            "value": "0.7400",
                            "weight": "0.3500",
                            "evidence_id": "event-9001",
                            "provenance": {
                                "source_type": "event_or_ai_evidence",
                                "label": "원천 이벤트/AI 근거",
                                "evidence_id": "event-9001",
                            },
                        },
                        {
                            "component": "momentum_score",
                            "value": "0.6100",
                            "weight": "0.2500",
                            "evidence_id": "market-feature-aapl-2024-11-01-return_since_first_observation",
                            "provenance": {
                                "source_type": "market_feature",
                                "label": "가격 feature snapshot",
                                "feature_code": "return_since_first_observation",
                                "feature_name": "Return Since First Observation",
                                "feature_value": "0.12000000",
                                "zscore": "0.44000000",
                                "as_of_date": "2024-11-01",
                                "source_run_id": 9201,
                                "evidence_json": {
                                    "feature_set_version": "bootstrap-v1",
                                    "universe_batch_id": 6101,
                                    "rank_position": 2,
                                    "observation_count": 22,
                                    "first_trade_date": "2024-10-01",
                                    "latest_trade_date": "2024-11-01",
                                    "as_of_date": "2024-11-01",
                                },
                            },
                        },
                        {
                            "component": "rank_score",
                            "value": "0.8800",
                            "weight": "0.1500",
                            "evidence_id": "universe-rank-aapl-2024-11-01-6101",
                            "provenance": {
                                "source_type": "strategy_universe_rank",
                                "label": "전략 유니버스 순위",
                                "universe_batch_id": 6101,
                                "rank_position": 2,
                                "universe_member_count": 10,
                                "selection_score": "0.9200",
                                "selection_rule": "liquid_large_cap_bootstrap",
                                "latest_trade_date": "2024-11-01",
                                "observation_count": 22,
                                "inclusion_reason": "liquidity and available price history",
                                "source_run_id": 9200,
                            },
                        },
                        {
                            "component": "short_term_score",
                            "value": "0.5400",
                            "weight": "0.1500",
                            "evidence_id": "market-feature-aapl-2024-11-01-return_1d",
                            "provenance": {
                                "source_type": "market_feature",
                                "label": "가격 feature snapshot",
                                "feature_code": "return_1d",
                                "feature_name": "One Day Return",
                                "feature_value": "0.01800000",
                                "zscore": "0.21000000",
                                "as_of_date": "2024-11-01",
                                "source_run_id": 9201,
                                "evidence_json": {
                                    "feature_set_version": "bootstrap-v1",
                                    "universe_batch_id": 6101,
                                    "rank_position": 2,
                                    "observation_count": 22,
                                    "first_trade_date": "2024-10-01",
                                    "latest_trade_date": "2024-11-01",
                                    "as_of_date": "2024-11-01",
                                },
                            },
                        },
                        {
                            "component": "macro_regime_score",
                            "value": "0.6700",
                            "weight": "0.0000",
                            "evidence_id": "cycle-stack-aapl-2024-11-01-macro_regime_score",
                            "provenance": {
                                "source_type": "cycle_stack_context",
                                "label": "계층형 사이클 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "cycle_stack_node_code": "MACRO_RATES_FED",
                                    "cycle_stack_level": "macro_regime",
                                    "cycle_stack_explanation": "Selected recommendation node: MACRO_RATES_FED.",
                                    "cycle_stack_note": "설명용 weight 0.",
                                },
                            },
                        },
                        {
                            "component": "domain_cycle_score",
                            "value": "0.6300",
                            "weight": "0.0000",
                            "evidence_id": "cycle-stack-aapl-2024-11-01-domain_cycle_score",
                            "provenance": {
                                "source_type": "cycle_stack_context",
                                "label": "계층형 사이클 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "cycle_stack_node_code": "TECH_DOMAIN",
                                    "cycle_stack_level": "domain",
                                    "cycle_stack_explanation": "Selected recommendation node: TECH_DOMAIN.",
                                },
                            },
                        },
                        {
                            "component": "theme_cycle_score",
                            "value": "0.6500",
                            "weight": "0.0000",
                            "evidence_id": "cycle-stack-aapl-2024-11-01-theme_cycle_score",
                            "provenance": {
                                "source_type": "cycle_stack_context",
                                "label": "계층형 사이클 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "cycle_stack_node_code": "AI_SEMICONDUCTOR_CYCLE",
                                    "cycle_stack_level": "theme",
                                    "cycle_stack_explanation": "Selected recommendation node: AI_SEMICONDUCTOR_CYCLE.",
                                },
                            },
                        },
                        {
                            "component": "instrument_cycle_score",
                            "value": "0.6200",
                            "weight": "0.0000",
                            "evidence_id": "cycle-stack-aapl-2024-11-01-instrument_cycle_score",
                            "provenance": {
                                "source_type": "cycle_stack_context",
                                "label": "계층형 사이클 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "cycle_stack_node_code": "AI_SEMICONDUCTOR_CYCLE",
                                    "cycle_stack_level": "instrument",
                                    "cycle_stack_explanation": "Selected recommendation node: AI_SEMICONDUCTOR_CYCLE.",
                                },
                            },
                        },
                        {
                            "component": "cycle_conflict_penalty",
                            "value": "0.0000",
                            "weight": "0.0000",
                            "evidence_id": "cycle-stack-aapl-2024-11-01-cycle_conflict_penalty",
                            "provenance": {
                                "source_type": "cycle_stack_context",
                                "label": "계층형 사이클 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "cycle_stack_node_code": "AI_SEMICONDUCTOR_CYCLE",
                                    "cycle_stack_level": "conflict",
                                    "cycle_stack_explanation": "Selected recommendation node: AI_SEMICONDUCTOR_CYCLE.",
                                },
                            },
                        },
                        {
                            "component": "fundamental_quality_score",
                            "value": "0.7200",
                            "weight": 0.0,
                            "evidence_id": "fundamental-aapl-2024-11-01-fundamental_quality_score",
                            "provenance": {
                                "source_type": "fundamental_context",
                                "label": "재무 품질 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "fundamental_component_name": "fundamental_quality_score",
                                    "fundamental_explanation": "Zero-weight financial quality component from normalized profitability, cash-flow quality, and peer context.",
                                    "fundamental_note": "전문가식 기업 분석 입력을 추천 상세에 노출하기 위한 zero-weight 검증 항목이다.",
                                },
                            },
                        },
                        {
                            "component": "valuation_margin_score",
                            "value": "0.5800",
                            "weight": "0.0000",
                            "evidence_id": "fundamental-aapl-2024-11-01-valuation_margin_score",
                            "provenance": {
                                "source_type": "fundamental_context",
                                "label": "밸류에이션 여유 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "fundamental_component_name": "valuation_margin_score",
                                    "fundamental_explanation": "Zero-weight valuation margin component from valuation_snapshot margin-of-safety context.",
                                },
                            },
                        },
                        {
                            "component": "peer_relative_score",
                            "value": "0.6400",
                            "weight": "0.0000",
                            "evidence_id": "fundamental-aapl-2024-11-01-peer_relative_score",
                            "provenance": {
                                "source_type": "fundamental_context",
                                "label": "피어 비교 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "fundamental_component_name": "peer_relative_score",
                                    "fundamental_explanation": "Zero-weight peer-relative component from peer percentile ranks.",
                                },
                            },
                        },
                        {
                            "component": "balance_sheet_risk_penalty",
                            "value": "0.7600",
                            "weight": "0.0000",
                            "evidence_id": "fundamental-aapl-2024-11-01-balance_sheet_risk_penalty",
                            "provenance": {
                                "source_type": "fundamental_context",
                                "label": "재무 안정성 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "fundamental_component_name": "balance_sheet_risk_penalty",
                                    "fundamental_explanation": "Zero-weight balance-sheet risk component; higher means lower observed leverage pressure.",
                                },
                            },
                        },
                        {
                            "component": "thesis_consistency_score",
                            "value": "0.8000",
                            "weight": "0.0000",
                            "evidence_id": "fundamental-aapl-2024-11-01-thesis_consistency_score",
                            "provenance": {
                                "source_type": "fundamental_context",
                                "label": "투자 논리 일관성 근거",
                                "evidence_json": {
                                    "as_of_date": "2024-11-01",
                                    "fundamental_component_name": "thesis_consistency_score",
                                    "fundamental_explanation": "Zero-weight thesis consistency component.",
                                },
                            },
                        },
	                    ],
                        "equity_research": {
                            "artifact_id": 1201,
                            "as_of_date": "2024-11-01",
                            "artifact_type": "full_equity_research",
                            "provider": "fixture",
                            "model_name": "codex-cli-default",
                            "title": "AAPL 기업 리서치 요약",
                            "korean_summary": "서비스 매출과 현금흐름 품질이 추천 근거를 보강한다.",
                            "key_points": ["서비스 매출 확대", "현금흐름 품질 양호"],
                            "catalysts": ["신제품 사이클"],
                            "risks": ["중국 수요 둔화"],
                            "invalidation_conditions": ["마진 훼손이 두 분기 지속"],
                            "valuation_sensitivity": {"margin_of_safety": "watch"},
	                        "source_document_ids": ["aapl-2024-10k-20240928"],
	                        "source_run_id": 7711,
	                        "created_at": "2024-11-01T09:00:00+00:00",
	                    },
                        "industry_competitive_position": {
                            "competitive_position_id": 4101,
                            "as_of_date": "2024-11-01",
                            "methodology": "peer_financial_proxy_v1",
                            "competitive_position": "leader",
                            "peer_group_id": 3101,
                            "peer_group_code": "large_cap_technology",
                            "peer_group_name": "Large Cap Technology",
                            "sector_code": "TECH_DOMAIN",
                            "sector_name": "Technology Domain",
                            "moat_score": "0.8200",
                            "pricing_power_score": "0.7800",
                            "profitability_score": "0.8400",
                            "growth_position_score": "0.7100",
                            "financial_strength_score": "0.9000",
                            "rivalry_risk_score": "0.4200",
                            "buyer_power_risk_score": "0.3800",
                            "supplier_power_risk_score": "0.3300",
                            "substitute_threat_risk_score": "0.2700",
                            "new_entry_threat_risk_score": "0.2400",
                            "capacity_cycle_risk_score": "0.3100",
                            "metric_coverage_count": 9,
                            "peer_count": 8,
                            "key_strengths": ["High profitability percentile", "Strong balance sheet"],
                            "key_risks": ["Large-cap technology rivalry remains material"],
                        "peer_context": {"profitability_percentile": "0.8400"},
                        "rationale": "Peer financial proxy ranks AAPL as a leader.",
                        "source_run_id": 779,
                    },
                    "financial_statement_model": {
                        "statement_scope": "annual",
                        "latest_period_end": "2024-09-28",
                        "latest_as_of_date": "2024-11-01",
                        "latest_fiscal_year": 2024,
                        "latest_fiscal_quarter": None,
                        "period_count": 4,
                        "metric_count": 6,
                        "computed_metric_count": 5,
                        "unavailable_metric_count": 1,
                        "insufficient_history_metric_count": 0,
                        "status_counts": [
                            {"metric_status": "computed", "metric_count": 5},
                            {"metric_status": "unavailable", "metric_count": 1},
                        ],
                        "source_run_ids": [778],
                        "metrics": [
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0610",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                            {
                                "metric_code": "operating_margin",
                                "metric_value": "0.3150",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Operating income divided by revenue.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                            {
                                "metric_code": "free_cash_flow_margin",
                                "metric_value": "0.2470",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Operating cash flow minus capex divided by revenue.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                            {
                                "metric_code": "free_cash_flow_to_net_income",
                                "metric_value": "1.1800",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Free cash flow divided by net income.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                            {
                                "metric_code": "liabilities_to_assets",
                                "metric_value": "0.8200",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Total liabilities divided by total assets.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                            {
                                "metric_code": "roic",
                                "metric_value": None,
                                "metric_unit": "ratio",
                                "metric_status": "unavailable",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Invested capital denominator is missing.",
                                "source_run_id": 778,
                                "created_at": "2024-11-01T10:10:00+00:00",
                            },
                        ],
                        "history": [
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0610",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2024,
                                "fiscal_quarter": None,
                                "period_end": "2024-09-28",
                                "as_of_date": "2024-11-01",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                            },
                            {
                                "metric_code": "revenue_growth_yoy",
                                "metric_value": "0.0280",
                                "metric_unit": "ratio",
                                "metric_status": "computed",
                                "statement_scope": "annual",
                                "fiscal_year": 2023,
                                "fiscal_quarter": None,
                                "period_end": "2023-09-30",
                                "as_of_date": "2024-11-01",
                                "rationale": "Current revenue divided by prior comparable annual revenue minus one.",
                                "source_run_id": 778,
                            },
                        ],
                        "share_count": {
                            "latest_period_end": "2024-09-28",
                            "latest_fiscal_year": 2024,
                            "latest_shares_outstanding": "15300000000",
                            "previous_period_end": "2023-09-30",
                            "previous_shares_outstanding": "15800000000",
                            "share_count_change_pct": "-0.0316",
                            "source_run_id": 778,
                        },
                    },
	                    "valuation_methods": [
	                        {
	                            "valuation_snapshot_id": 5101,
	                            "as_of_date": "2024-11-01",
	                            "method": "dcf_lite",
	                            "base_price": "240.0000",
	                            "fair_value_low": "210.0000",
	                            "fair_value_base": "270.0000",
	                            "fair_value_high": "315.0000",
	                            "margin_of_safety": "0.1250",
	                            "assumptions": {"method_description": "Discounted cash flow-lite"},
	                            "confidence": "0.6200",
	                            "source_run_id": 7801,
	                            "created_at": "2024-11-01T10:00:00+00:00",
	                        },
	                        {
	                            "valuation_snapshot_id": 5102,
	                            "as_of_date": "2024-11-01",
	                            "method": "relative_multiple",
	                            "base_price": "240.0000",
	                            "fair_value_low": "220.0000",
	                            "fair_value_base": "255.0000",
	                            "fair_value_high": "290.0000",
	                            "margin_of_safety": "0.0625",
	                            "assumptions": {"method_description": "Peer multiple comparison"},
	                            "confidence": "0.5800",
	                            "source_run_id": 7801,
	                            "created_at": "2024-11-01T10:00:00+00:00",
	                        },
	                        {
	                            "valuation_snapshot_id": 5103,
	                            "as_of_date": "2024-11-01",
	                            "method": "scenario_range",
	                            "base_price": "240.0000",
	                            "fair_value_low": "200.0000",
	                            "fair_value_base": "260.0000",
	                            "fair_value_high": "330.0000",
	                            "margin_of_safety": "0.0833",
	                            "assumptions": {"method_description": "Bear/base/bull scenario range"},
	                            "confidence": "0.6000",
	                            "source_run_id": 7801,
	                            "created_at": "2024-11-01T10:00:00+00:00",
	                        },
	                    ],
	                    "linked_thesis_id": 7001,
	                    "evidence_trace": {
	                        "direct_news_or_ai": {
	                            "status": "linked",
	                            "evidence_id": "ai-evidence-8801",
	                            "event_id": 9001,
	                            "artifact_id": 8801,
	                            "title": "AAPL annual report event",
	                            "korean_title": "AAPL 연례 보고서 이벤트",
	                            "korean_summary": "연례 보고서 이벤트 품질이 우호적으로 유지된다.",
	                            "translation_confidence": "0.9100",
	                            "event_at": "2024-10-31T14:00:00+00:00",
	                            "impact_direction": "supportive",
	                            "impact_strength": "0.7000",
	                            "confidence": "0.8400",
	                            "rationale": "Annual report event quality remains supportive.",
	                        },
	                        "macro_flow": {
	                            "status": "linked",
	                            "propagated_impact_count": 2,
	                            "source_run_id": 9301,
	                            "recent_flows": [
	                                {
	                                    "event_id": 9101,
	                                    "title": "Fed rate path supports long-duration technology",
	                                    "korean_title": "연준 금리 경로가 장기 성장 기술주를 지지한다",
	                                    "korean_summary": "금리 경로 변화가 기술주 노출도에 우호적으로 전파된다.",
	                                    "translation_confidence": "0.8900",
	                                    "event_at": "2024-10-30T12:00:00+00:00",
	                                    "theme_key": "MACRO_RATES_FED",
	                                    "theme_name": "Fed rates",
	                                    "impact_direction": "supportive",
	                                    "impact_strength": "0.5200",
	                                    "confidence": "0.7700",
	                                    "exposure_weight": "0.6500",
	                                }
	                            ],
	                        },
	                        "holding_review": {
	                            "status": "review_linked",
	                            "portfolio_name": "Long Term Paper",
	                            "portfolio_review_id": 6001,
	                            "review_item_id": 6101,
	                            "review_date": "2024-11-01",
	                            "review_source": "deterministic_bootstrap",
	                            "risk_level": "moderate",
	                            "source_run_id": 9401,
	                            "action": "monitor",
	                            "reason": "Position is within target range.",
	                            "priority": 2,
	                            "health_score": "0.7200",
	                            "current_weight": "0.0500",
	                            "recommended_weight": "0.0550",
	                            "weight_gap": "0.0050",
	                            "market_value": "2500.00",
	                            "position_snapshot_date": "2024-11-01",
	                            "position_source_run_id": 9400,
	                            "position_linked_thesis_id": 7001,
	                        },
	                    },
	                    "outcome": {
                        "measurement_end_date": "2024-12-02",
                        "absolute_return": "0.1000",
                        "benchmark_return": "0.0400",
                        "alpha": "0.0600",
                        "label": "outperform",
                    },
                }
            )
        if sql.startswith("-- frontend recommendation list state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-11-01",
                    "strategy_name": "long_term_core",
                    "horizon_type": "long_term",
                    "universe_version": "bootstrap-v1",
                    "recommendation_count": 2,
                    "summary": {
                        "active_count": 2,
                        "reviewable_count": 1,
                        "blocked_count": 1,
                        "measured_count": 1,
                        "linked_thesis_count": 1,
                        "ai_or_event_evidence_count": 1,
                        "macro_flow_evidence_recommendation_count": 1,
                        "decision_review_ready_count": 1,
                        "paper_validation_pending_count": 0,
                        "decision_blocked_count": 1,
                        "order_blocked_count": 2,
                        "evidence_quality_ready_count": 1,
                        "evidence_quality_gap_count": 0,
                        "evidence_quality_source_blocked_count": 1,
                        "average_score": "0.5189",
                    },
                    "recommendations": [
                        {
                            "recommendation_id": 7101,
                            "symbol": "AAPL",
                            "name": "Apple Inc.",
                            "instrument_id": 501,
                            "as_of_date": "2024-11-01",
                            "rank_position": 1,
                            "bucket": "core",
                            "action": "monitor_or_accumulate",
                            "status": "active",
                            "score": "0.7800",
                            "recommended_weight": "0.0500",
                            "linked_thesis_id": 7001,
                            "evidence": {
                                "score_component_count": 4,
                                "ai_or_event_component_count": 1,
                                "market_or_rank_component_count": 3,
                                "macro_flow_component_count": 1,
                                "macro_flow_evidence_count": 8,
                                "quality_status": "ai_review_passed",
                                "primary_evidence_id": "ai-evidence-8801",
                            },
                            "evidence_quality": {
                                "status": "ready_for_review",
                                "summary": "핵심 추천 근거가 연결됐다. 그래도 추천 weight와 주문은 바꾸지 않는다.",
                                "product_type": "operating_company",
                                "coverage_ratio": "1.0000",
                                "available_layer_count": 9,
                                "expected_layer_count": 9,
                                "missing_layer_count": 0,
                                "blocked_layer_count": 0,
                                "pending_layer_count": 0,
                                "missing_layers": [],
                                "paper_validation_status": "measured",
                                "source_blocker": {
                                    "blocked": False,
                                    "blocker_code": "",
                                    "blocker_label": "",
                                    "summary": "",
                                },
                            },
                            "outcome": {
                                "measurement_end_date": "2024-12-02",
                                "label": "outperform",
                                "alpha": "0.0600",
                            },
                            "decision_boundary": {
                                "status": "decision_review_ready",
                                "reason": "근거와 투자 논리가 연결되어 추천 상세 검토로 들어갈 수 있다.",
                                "paper_validation_input_allowed": True,
                                "automatic_order_allowed": False,
                                "broker_submit_allowed": False,
                                "order_boundary": "read_only_no_order",
                            },
                        },
                        {
                            "recommendation_id": 7102,
                            "symbol": "BABA",
                            "name": "Alibaba Group Holding Limited",
                            "instrument_id": 502,
                            "as_of_date": "2024-11-01",
                            "rank_position": 2,
                            "bucket": "avoid",
                            "action": "exclude",
                            "status": "active",
                            "score": "0.2579",
                            "recommended_weight": "0",
                            "linked_thesis_id": None,
                            "evidence": {
                                "score_component_count": 2,
                                "ai_or_event_component_count": 0,
                                "market_or_rank_component_count": 2,
                                "macro_flow_component_count": 0,
                                "macro_flow_evidence_count": 0,
                                "quality_status": "blocked",
                                "primary_evidence_id": None,
                            },
                            "evidence_quality": {
                                "status": "source_blocked",
                                "summary": "표준 재무 원천이 차단되어 전문 판단과 페이퍼 검증 입력에서 제외한다.",
                                "product_type": "operating_company",
                                "coverage_ratio": "0.3333",
                                "available_layer_count": 3,
                                "expected_layer_count": 9,
                                "missing_layer_count": 6,
                                "blocked_layer_count": 2,
                                "pending_layer_count": 0,
                                "missing_layers": [
                                    "macro_cycle",
                                    "news_ai",
                                    "financial_metric_normalized",
                                    "active_thesis",
                                    "paper_validation",
                                ],
                                "paper_validation_status": "blocked_source",
                                "source_blocker": {
                                    "blocked": True,
                                    "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                                    "blocker_label": "SEC us-gaap facts 없음",
                                    "summary": "facts.us-gaap missing",
                                },
                            },
                            "outcome": {
                                "measurement_end_date": None,
                                "label": "unmeasured",
                                "alpha": None,
                            },
                            "decision_boundary": {
                                "status": "blocked_missing_thesis",
                                "reason": "투자 논리가 없어 추천 검토 입력으로 쓰면 안 된다.",
                                "paper_validation_input_allowed": False,
                                "automatic_order_allowed": False,
                                "broker_submit_allowed": False,
                                "order_boundary": "read_only_no_order",
                            },
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend thesis detail state lookup"):
            return json.dumps(
                {
                    "thesis_id": 7001,
                    "symbol": "AAPL",
                    "instrument_id": 501,
                    "status": "active",
                    "thesis_version": "bootstrap-v1",
                    "created_from_recommendation_id": 7101,
                    "summary": "AAPL remains covered by annual reporting quality.",
                    "entry_conditions": "Service revenue keeps compounding; Free cash flow quality remains durable",
                    "exit_conditions": "Capital returns weaken materially",
                    "core_claims": [
                        "Annual reporting event quality remains supportive.",
                        "Cycle state is constructive for the long-term horizon.",
                    ],
                    "invalidation_conditions": [
                        {
                            "condition": "cycle_state_breaks_to_negative",
                            "current_status": "not_triggered",
                        }
                    ],
                    "latest_review": {
                        "review_id": 8001,
                        "action": "monitor",
                        "risk_level": "low",
                        "reviewed_at": "2024-11-01T23:00:00+00:00",
                        "summary": "AAPL 검토 결과: 조치 watch, 건강 점수 0.3610.",
                        "change_notes": "검토 근거: 아직 관찰 후보 (watchlist_recommendation). 적용 조치: watch. thesis 상태는 자동 변경하지 않았고, 주문이나 가상 거래도 만들지 않았다.",
                        "next_review_date": "2024-12-01",
                    },
                    "equity_research": {
                        "artifact_id": 1201,
                        "as_of_date": "2024-11-01",
                        "artifact_type": "full_equity_research",
                        "provider": "fixture",
                        "model_name": "codex-cli-default",
                        "title": "AAPL 기업 리서치 요약",
                        "korean_summary": "서비스 매출과 현금흐름 품질이 장기 투자 논리를 보강한다.",
                        "key_points": ["서비스 매출 확대", "현금흐름 품질 양호"],
                        "catalysts": ["신제품 사이클"],
                        "risks": ["중국 수요 둔화"],
                        "invalidation_conditions": ["마진 훼손이 두 분기 지속"],
                        "valuation_sensitivity": {
                            "margin_of_safety": "watch",
                            "upside_case": "서비스 성장 유지",
                        },
                        "source_document_ids": ["aapl-2024-10k-20240928"],
                        "source_run_id": 7711,
                        "created_at": "2024-11-01T09:00:00+00:00",
                    },
                    "valuation_methods": [
                        {
                            "valuation_snapshot_id": 5101,
                            "as_of_date": "2024-11-01",
                            "method": "dcf_lite",
                            "base_price": "240.0000",
                            "fair_value_low": "210.0000",
                            "fair_value_base": "270.0000",
                            "fair_value_high": "315.0000",
                            "margin_of_safety": "0.1250",
                            "assumptions": {"method_description": "Discounted cash flow-lite"},
                            "confidence": "0.6200",
                            "source_run_id": 7801,
                            "created_at": "2024-11-01T10:00:00+00:00",
                        },
                        {
                            "valuation_snapshot_id": 5102,
                            "as_of_date": "2024-11-01",
                            "method": "relative_multiple",
                            "base_price": "240.0000",
                            "fair_value_low": "220.0000",
                            "fair_value_base": "255.0000",
                            "fair_value_high": "290.0000",
                            "margin_of_safety": "0.0625",
                            "assumptions": {"method_description": "Peer multiple comparison"},
                            "confidence": "0.5800",
                            "source_run_id": 7801,
                            "created_at": "2024-11-01T10:00:00+00:00",
                        },
                        {
                            "valuation_snapshot_id": 5103,
                            "as_of_date": "2024-11-01",
                            "method": "scenario_range",
                            "base_price": "240.0000",
                            "fair_value_low": "200.0000",
                            "fair_value_base": "260.0000",
                            "fair_value_high": "330.0000",
                            "margin_of_safety": "0.0833",
                            "assumptions": {"method_description": "Bear/base/bull scenario range"},
                            "confidence": "0.6000",
                            "source_run_id": 7801,
                            "created_at": "2024-11-01T10:00:00+00:00",
                        },
                    ],
                    "evidence": [
                        {
                            "evidence_id": 9001,
                            "type": "source_document_event",
                            "title": "AAPL 2024 10-K annual reporting event",
                            "observed_at": "2024-10-31T14:00:00+00:00",
                        },
                        {
                            "evidence_id": 8101,
                            "type": "performance_outcome",
                            "title": "AAPL outperformed SPY over measurement window",
                            "observed_at": "2024-12-02",
                        },
                    ],
                }
            )
        if sql.startswith("-- frontend ai evidence detail state lookup"):
            if "ai-evidence-3" in sql:
                return json.dumps(
                    {
                        "evidence_id": 3,
                        "title": "Nvidia H200 export path remains open",
                        "evidence_type": "news_event_candidate",
                        "event_at": "2026-05-19T10:02:40+00:00",
                        "instrument": {"symbol": "NVDA", "instrument_id": 504},
                        "source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                        "classification": {
                            "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                            "theme_name": "AI Semiconductor Cycle",
                            "impact_direction": "supportive",
                            "impact_score": "0.7400",
                        },
                        "extraction_run": {
                            "run_id": 96,
                            "status": "succeeded",
                            "provider": "codex_oauth",
                            "model_id": "codex-cli",
                            "prompt_version": "news_event_candidate_v1",
                            "finished_at": "2026-05-19T11:30:00+00:00",
                            "input_tokens": 120,
                            "output_tokens": 80,
                            "estimated_cost_usd": "0.0000",
                            "quality_gate": "ai_review_passed",
                        },
                        "extracted_fields": [
                            {
                                "field": "event_summary",
                                "value": "Nvidia H200 export path remains open.",
                                "confidence": "0.8600",
                                "source_chunk_id": "news-ai-candidate",
                            }
                        ],
                        "news_candidate": {
                            "analysis_method": "fixture_structured_news",
                            "event_summary": "Nvidia H200 export path remains open, supporting AI semiconductor demand visibility.",
                            "theme_impacts": [
                                {
                                    "theme_code": "AI_SEMICONDUCTOR_CYCLE",
                                    "impact_direction": "supportive",
                                    "impact_strength": "0.7400",
                                    "confidence": "0.8800",
                                    "rationale": "The headline and summary directly mention Nvidia H200 GPU export continuity.",
                                    "evidence_summary": "Nvidia H200 China deal survived the summit.",
                                }
                            ],
                            "instrument_impacts": [
                                {
                                    "symbol": "NVDA",
                                    "impact_direction": "supportive",
                                    "impact_strength": "0.7200",
                                    "confidence": "0.8600",
                                    "rationale": "The article directly names Nvidia and H200 GPUs.",
                                    "evidence_summary": "Nvidia H200 export path stays open.",
                                }
                            ],
                            "uncertainty_notes": "RSS summary is short, so downstream scoring should treat this as evidence, not a recommendation.",
                            "recommendation_relevance": "watchlist",
                        },
                        "retrieval_context_summary": {
                            "as_of_date": "2026-05-19",
                            "known_themes": [{"code": "AI_SEMICONDUCTOR_CYCLE"}],
                            "theme_edges": [{"source": "AI_SEMICONDUCTOR_CYCLE", "target": "SEMICONDUCTOR_CAPEX"}],
                            "current_event_impacts": [{"event_id": 20}],
                            "recent_similar_events": [{"event_id": 18}],
                        },
                        "source_chunks": [],
                    }
                )
            if "ai-evidence-2" in sql:
                return json.dumps(
                    {
                        "evidence_id": 2,
                        "title": "News cluster summary: AI_SEMICONDUCTOR_CYCLE",
                        "evidence_type": "news_cluster_summary",
                        "event_at": "2026-05-19T10:02:40+00:00",
                        "instrument": {"symbol": "NVDA", "instrument_id": 504},
                        "source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                        "classification": {
                            "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                            "theme_name": "AI Semiconductor Cycle",
                            "impact_direction": "supportive",
                            "impact_score": "0.6600",
                        },
                        "extraction_run": {
                            "run_id": 95,
                            "status": "succeeded",
                            "provider": "local_rules",
                            "model_id": "news_cluster_summary_v1",
                            "prompt_version": "news_cluster_summary_v1",
                            "finished_at": "2026-05-19T11:20:00+00:00",
                            "input_tokens": 0,
                            "output_tokens": 0,
                            "estimated_cost_usd": "0.0000",
                            "quality_gate": "ai_review_passed",
                        },
                        "extracted_fields": [
                            {
                                "field": "analysis_method",
                                "value": "free_local_rules",
                                "confidence": "1.0000",
                                "source_chunk_id": "news-cluster-local-rules",
                            }
                        ],
                        "cluster_summary": {
                            "as_of_date": "2026-05-19",
                            "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                            "theme_name": "AI Semiconductor Cycle",
                            "story_key": "theme",
                            "story_label": "AI Semiconductor Cycle",
                            "event_count": 10,
                            "symbols": ["NVDA"],
                            "direction_counts": {"supportive": 1, "watch": 9},
                            "representative_event_id": 20,
                            "request_hash": "hash-fixture",
                        },
                        "cluster_events": [
                            {
                                "event_id": 20,
                                "title": "The Nvidia H200 China deal survived the Trump-Xi summit",
                                "event_at": "2026-05-19T10:02:40+00:00",
                                "symbol": "NVDA",
                                "impact_direction": "supportive",
                                "impact_score": 0.66,
                                "source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                            }
                        ],
                        "source_chunks": [],
                    }
                )
            return json.dumps(
                {
                    "evidence_id": 8801,
                    "title": "AAPL 2024 10-K annual reporting event",
                    "evidence_type": "source_document_event",
                    "event_at": "2024-09-28T00:00:00+00:00",
                    "instrument": {"symbol": "AAPL", "instrument_id": 501},
                    "source_document_id": "aapl-2024-10k-20240928",
                    "classification": {
                        "theme_key": "ANNUAL_REPORTING",
                        "theme_name": "Annual Reporting",
                        "impact_direction": "supportive",
                        "impact_score": "0.8200",
                    },
                    "extraction_run": {
                        "run_id": 9201,
                        "status": "succeeded",
                        "provider": "openai",
                        "model_id": "responses-frontier-placeholder",
                        "prompt_version": "event-extraction-v0.1",
                        "finished_at": "2024-10-01T02:15:00+00:00",
                        "input_tokens": 4218,
                        "output_tokens": 642,
                        "estimated_cost_usd": "0.0184",
                        "quality_gate": "ai_review_passed",
                    },
                    "extracted_fields": [
                        {
                            "field": "event_title",
                            "value": "Annual filing confirms services revenue mix.",
                            "confidence": "0.8600",
                            "source_chunk_id": "business-overview",
                        }
                    ],
                    "source_chunks": [
                        {
                            "chunk_id": "business-overview",
                            "section": "Business overview",
                            "locator": "10-K item 1",
                            "summary": "Company overview and segment framing.",
                            "relevance": "entity_and_theme_anchor",
                        }
                    ],
                }
                )
        if sql.startswith("-- frontend ai news cluster list state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2026-05-19",
                    "summary": {
                        "cluster_count": 1,
                        "clustered_event_count": 10,
                        "source_document_count": 2,
                        "chunk_count": 2,
                        "embedded_chunk_count": 2,
                        "local_rule_cluster_count": 1,
                        "llm_candidate_invocation_count": 5,
                        "llm_candidate_success_count": 3,
                        "llm_candidate_failed_count": 2,
                        "llm_candidate_artifact_count": 3,
                        "latest_llm_invocation_status": "failed",
                        "latest_llm_invocation_at": "2026-05-19T11:30:00+00:00",
                        "latest_llm_success_at": "2026-05-19T10:30:00+00:00",
                        "latest_llm_failure_at": "2026-05-19T11:30:00+00:00",
                        "latest_llm_provider": "codex_oauth",
                        "estimated_cost_usd": "0.0000",
                    },
                    "clusters": [
                        {
                            "evidence_id": 2,
                            "title": "News cluster summary: AI_SEMICONDUCTOR_CYCLE",
                            "evidence_type": "news_cluster_summary",
                            "created_at": "2026-05-19T11:20:00+00:00",
                            "confidence": "0.9100",
                            "cluster_summary": {
                                "as_of_date": "2026-05-19",
                                "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                                "theme_name": "AI Semiconductor Cycle",
                                "story_key": "theme",
                                "story_label": "AI Semiconductor Cycle",
                                "event_count": 10,
                                "symbols": ["NVDA"],
                                "direction_counts": {"supportive": 1, "watch": 9},
                                "representative_event_id": 20,
                                "request_hash": "hash-fixture",
                            },
                            "cluster_events": [
                                {
                                    "event_id": 20,
                                    "title": "The Nvidia H200 China deal survived the Trump-Xi summit",
                                    "event_at": "2026-05-19T10:02:40+00:00",
                                    "symbol": "NVDA",
                                    "impact_direction": "supportive",
                                    "impact_score": 0.66,
                                    "source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                                }
                            ],
                            "audit_notes": ["No paid provider or LLM was called."],
                            "representative_source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                            "source_document_count": 2,
                            "chunk_count": 2,
                            "embedded_chunk_count": 2,
                            "extraction_run": {
                                "run_id": 95,
                                "status": "succeeded",
                                "provider": "local_rules",
                                "model_id": "news_cluster_summary_v1",
                                "reasoning_effort": None,
                                "input_tokens": 0,
                                "output_tokens": 0,
                                "estimated_cost_usd": "0.0000",
                                "request_hash": "hash-fixture",
                            },
                            "source_documents": [
                                {
                                    "source_document_id": "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
                                    "title": "The Nvidia H200 China deal survived the Trump-Xi summit",
                                    "url": "https://example.com/nvda-h200",
                                    "published_at": "2026-05-19T10:02:40+00:00",
                                    "chunk_count": 1,
                                    "embedded_chunk_count": 1,
                                }
                            ],
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend source document detail state lookup"):
            return json.dumps(
                {
                    "document_id": "aapl-2024-10k-20240928",
                    "title": "AAPL 2024 Form 10-K source document",
                    "source_type": "sec_filing",
                    "publisher": "SEC EDGAR",
                    "symbol": "AAPL",
                    "cik": "0000320193",
                    "form_type": "10-K",
                    "period_end": "2024-09-28",
                    "filed_at": "2024-11-01T00:00:00+00:00",
                    "accession_id": "aapl-2024-10k-fixture",
                    "storage_uri": "artifact://sec/aapl/2024/10-k/raw.txt",
                    "checksum": "sha256:fixture-aapl-2024-10k",
                    "retrieval": {
                        "source_run_id": 9301,
                        "fetched_at": "2024-11-01T01:10:00+00:00",
                        "parser_version": "sec-raw-fetch-v0.1",
                    },
                    "excerpts": [
                        {
                            "chunk_id": "business-overview",
                            "section": "Business overview",
                            "locator": "10-K item 1",
                            "summary": "Entity, segment, and product context.",
                        }
                    ],
                    "linked_evidence": [
                        {
                            "evidence_id": 8801,
                            "evidence_type": "source_document_event",
                            "title": "AAPL 2024 10-K annual reporting event",
                        }
                    ],
                }
            )
        if sql.startswith("-- portfolio remediation ticket report"):
            return json.dumps(
                {
                    "report_name": "portfolio_remediation_ticket_report",
                    "portfolio_name": "Long Term Paper",
                    "limit": 50,
                    "status_filter": "open",
                    "ticket_count": 1,
                    "status_counts": {"open": 1},
                    "remediation_type_counts": {"thesis_remediation": 1},
                    "action_counts": {"needs_thesis_review": 1},
                    "tickets": [
                        {
                            "remediation_ticket_id": 42,
                            "portfolio_review_id": 6001,
                            "instrument_id": 502,
                            "portfolio_name": "Long Term Paper",
                            "review_date": "2024-11-01",
                            "review_source": "coverage_gate",
                            "symbol": "BABA",
                            "action": "needs_thesis_review",
                            "remediation_type": "thesis_remediation",
                            "suggested_runner": "thesis_or_position_link_review",
                            "suggested_next_step": "Create or link an active thesis before the next portfolio review.",
                            "status": "open",
                            "priority": 1,
                            "risk_level": "high",
                            "health_score": "0.0000",
                            "current_weight": "0.0300",
                            "recommended_weight": None,
                            "reason": "coverage status missing_thesis",
                            "source_run_id": 9101,
                            "source_run_status": "succeeded",
                            "opened_at": "2024-11-01T23:30:00+00:00",
                            "updated_at": "2024-11-01T23:30:00+00:00",
                            "last_seen_at": "2024-11-01T23:30:00+00:00",
                            "resolved_at": None,
                        }
                    ],
                }
            )
        if sql.startswith("-- frontend remediation allocation policy lookup"):
            return json.dumps(
                {
                    "allocation_policy_id": 7001,
                    "policy_name": "global_default_long_term_guardrail",
                    "status": "active",
                    "policy_scope": "global",
                    "max_single_position_weight": "0.2500",
                    "min_rebalance_target_weight": "0.1000",
                    "valid_from": "2024-01-01",
                    "valid_to": None,
                    "rationale": "Default review-only guardrail.",
                }
            )
        if sql.startswith("-- frontend portfolio concentration exposure lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2024-11-01",
                    "position_weight_total": "0.0800",
                    "sector_exposures": [
                        {
                            "exposure_key": "TECHNOLOGY",
                            "exposure_name": "Technology",
                            "exposure_weight": "0.0500",
                            "position_count": 1,
                            "symbols": ["AAPL"],
                        },
                        {
                            "exposure_key": "CONSUMER_INTERNET",
                            "exposure_name": "Consumer Internet",
                            "exposure_weight": "0.0300",
                            "position_count": 1,
                            "symbols": ["BABA"],
                        },
                    ],
                    "theme_exposures": [
                        {
                            "exposure_key": "ANNUAL_REPORTING",
                            "exposure_name": "Annual Reporting",
                            "exposure_weight": "0.0500",
                            "position_count": 1,
                            "symbols": ["AAPL"],
                        },
                        {
                            "exposure_key": "CHINA_ADR_COVERAGE",
                            "exposure_name": "China ADR Coverage",
                            "exposure_weight": "0.0300",
                            "position_count": 1,
                            "symbols": ["BABA"],
                        },
                    ],
                    "unclassified_weight": "0.0000",
                    "unclassified_symbols": [],
                }
            )
        if sql.startswith("-- frontend portfolio review feedback calibration lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 54,
                    "created_at": "2026-05-27T04:00:00+00:00",
                    "eval_name": "portfolio_review_feedback_calibration",
                    "dataset_version": "portfolio-review-feedback-calibration-v1",
                    "as_of_date": "2026-05-27",
                    "portfolio_name": "Long Term Paper",
                    "lookback_days": 365,
                    "min_feedback_runs": 3,
                    "min_mature_decisions": 10,
                    "max_contradiction_rate": "0.15",
                    "calibration_status": "insufficient_history",
                    "feedback_run_count": 1,
                    "decision_count": 1,
                    "mature_decision_count": 0,
                    "too_early_count": 1,
                    "validated_count": 0,
                    "contradicted_count": 0,
                    "needs_more_data_count": 0,
                    "contradiction_rate": "0.0",
                    "validated_rate": "0.0",
                    "status_counts": {"too_early": 1},
                    "family_summaries": [
                        {
                            "decision_family": "benchmark_drift",
                            "decision_count": 1,
                            "mature_decision_count": 0,
                            "too_early_count": 1,
                            "validated_count": 0,
                            "contradicted_count": 0,
                            "needs_more_data_count": 0,
                            "contradiction_rate": "0.0",
                            "status_counts": {"too_early": 1},
                        }
                    ],
                    "decision_type_summaries": [
                        {
                            "decision_type": "reduce_watch",
                            "decision_count": 1,
                            "mature_decision_count": 0,
                            "too_early_count": 1,
                            "validated_count": 0,
                            "contradicted_count": 0,
                            "needs_more_data_count": 0,
                            "contradiction_rate": "0.0",
                            "status_counts": {"too_early": 1},
                        }
                    ],
                    "symbol_summaries": [
                        {
                            "symbol": "TSLA",
                            "decision_count": 1,
                            "mature_decision_count": 0,
                            "too_early_count": 1,
                            "validated_count": 0,
                            "contradicted_count": 0,
                            "needs_more_data_count": 0,
                            "contradiction_rate": "0.0",
                            "status_counts": {"too_early": 1},
                        }
                    ],
                    "latest_feedback_runs": [
                        {
                            "eval_run_id": 53,
                            "created_at": "2026-05-27T03:00:00+00:00",
                            "as_of_date": "2026-05-27",
                            "feedback_status": "too_early",
                            "decision_count": 1,
                            "too_early_count": 1,
                            "validated_count": 0,
                            "contradicted_count": 0,
                            "needs_more_data_count": 0,
                        }
                    ],
                    "guardrails": {
                        "recommendation_scoring_mutated": False,
                        "benchmark_definition_mutated": False,
                        "portfolio_position_mutated": False,
                        "automatic_rebalance_allowed": False,
                        "automatic_order_allowed": False,
                        "broker_submit_allowed": False,
                        "order_boundary": "read_only_no_order",
                    },
                    "next_action": "feedback을 더 쌓는다.",
                }
            )
        if sql.startswith("-- frontend portfolio review feedback cadence lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 55,
                    "created_at": "2026-05-27T05:00:00+00:00",
                    "eval_name": "portfolio_review_feedback_cadence",
                    "dataset_version": "portfolio-review-feedback-cadence-v1",
                    "as_of_date": "2026-05-27",
                    "portfolio_name": "Long Term Paper",
                    "min_horizon_days": 30,
                    "cadence_status": "wait_for_outcome_window",
                    "action_type": "wait",
                    "should_run_now": False,
                    "should_wait": True,
                    "wait_until": "2026-06-24",
                    "command": "성과 window가 닫힌 뒤 다시 cadence를 계산한다.",
                    "follow_up_command": "",
                    "label": "성과 관찰 기간 대기",
                    "reason": "최신 검토 이력이 아직 최소 30일 관찰 기간을 채우지 못했다.",
                    "history": {
                        "status": "loaded",
                        "eval_run_id": 52,
                        "as_of_date": "2026-05-25",
                        "decision_count": 2,
                    },
                    "feedback": {
                        "status": "loaded",
                        "eval_run_id": 53,
                        "feedback_status": "too_early",
                        "source_history_eval_run_id": 52,
                    },
                    "calibration": {
                        "status": "loaded",
                        "eval_run_id": 54,
                        "calibration_status": "insufficient_history",
                        "latest_feedback_runs": [{"eval_run_id": 53}],
                    },
                    "evidence": {
                        "history_age_days": 2,
                        "decision_count": 2,
                        "recommendation_outcome_count": 0,
                        "price_evidence_count": 2,
                        "paper_validation": {
                            "paper_validation_run_id": 12,
                            "validation_date": "2026-05-27",
                            "status": "completed",
                            "recommendation_count": 2,
                            "conflict_count": 0,
                            "approved_action_count": 0,
                        },
                    },
                    "blocks_weight_review": True,
                    "recommendation_scoring_mutated": False,
                    "benchmark_definition_mutated": False,
                    "portfolio_position_mutated": False,
                    "automatic_weight_change_allowed": False,
                    "automatic_rebalance_allowed": False,
                    "automatic_order_allowed": False,
                    "broker_submit_allowed": False,
                    "order_boundary": "read_only_no_order",
                    "next_action": "성과 관찰 기간이 끝난 뒤 feedback과 calibration을 다시 판단한다.",
                }
            )
        if sql.startswith("-- frontend portfolio review feedback action router lookup"):
            return json.dumps(
                {
                    "status": "loaded",
                    "eval_run_id": 56,
                    "created_at": "2026-05-27T06:00:00+00:00",
                    "eval_name": "portfolio_review_feedback_action_router",
                    "dataset_version": "portfolio-review-feedback-action-router-v1",
                    "as_of_date": "2026-05-27",
                    "portfolio_name": "Long Term Paper",
                    "source_cadence_status": "loaded",
                    "source_cadence_eval_run_id": 55,
                    "source_cadence_created_at": "2026-05-27T05:00:00+00:00",
                    "source_cadence_as_of_date": "2026-05-27",
                    "cadence_status": "wait_for_outcome_window",
                    "source_action_type": "wait",
                    "source_should_run_now": False,
                    "route_action": "no_op",
                    "action_status": "no_op_wait_for_outcome_window",
                    "reason": "decision history has not reached the minimum outcome observation window.",
                    "history_eval_run_id": 52,
                    "feedback_eval_run_id": 53,
                    "calibration_eval_run_id": 54,
                    "source_cadence": {
                        "as_of_date": "2026-05-27",
                        "cadence_status": "wait_for_outcome_window",
                        "action_type": "wait",
                        "should_run_now": False,
                        "should_wait": True,
                        "command": "성과 window가 닫힌 뒤 다시 cadence를 계산한다.",
                        "follow_up_command": "",
                    },
                    "child_runner": {
                        "executed": False,
                        "report_name": "",
                        "status": "not_run",
                        "run_id": None,
                        "eval_run_id": None,
                    },
                    "recommendation_scoring_mutated": False,
                    "benchmark_definition_mutated": False,
                    "portfolio_position_mutated": False,
                    "automatic_weight_change_allowed": False,
                    "automatic_rebalance_allowed": False,
                    "automatic_order_allowed": False,
                    "broker_submit_allowed": False,
                    "order_boundary": "read_only_no_order",
                    "next_action": "성과 관찰 기간이 끝날 때까지 기다린다.",
                }
            )
        if sql.startswith("-- portfolio outcome coverage report"):
            return json.dumps(
                {
                    "portfolio_id": 3001,
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2024-11-01",
                    "measurement_end_date": "2024-12-02",
                    "position_count": 2,
                    "status_counts": {
                        "covered": 1,
                        "missing_outcome": 0,
                        "missing_thesis": 1,
                        "missing_weight": 0,
                    },
                    "weight_by_status": {
                        "covered": "0.0500",
                        "missing_outcome": "0.0000",
                        "missing_thesis": "0.0300",
                        "missing_weight": "0.0000",
                    },
                    "cash_weight": "0.9200",
                    "coverage_ratio_by_weight": "0.6250",
                    "positions": [
                        {
                            "symbol": "AAPL",
                            "instrument_id": 501,
                            "coverage_status": "covered",
                            "weight": "0.0500",
                            "market_value": "2229.10",
                            "linked_thesis_id": 7001,
                            "thesis_title": "AAPL watch thesis via Annual Reporting",
                            "outcome_id": 8101,
                            "outcome_status": "working",
                            "success_grade": "pass",
                        },
                        {
                            "symbol": "BABA",
                            "instrument_id": 502,
                            "coverage_status": "missing_thesis",
                            "weight": "0.0300",
                            "market_value": "298.50",
                            "linked_thesis_id": None,
                            "thesis_title": None,
                            "outcome_id": None,
                            "outcome_status": None,
                            "success_grade": None,
                        },
                    ],
                }
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


class EmptyPortfolioCoverageExecutor(FakeLiveExecutor):
    def execute_scalar(self, sql: str) -> str:
        if sql.startswith("-- portfolio outcome coverage report"):
            return json.dumps(
                {
                    "portfolio_id": None,
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2026-05-20",
                    "measurement_end_date": "2026-06-20",
                    "position_count": 0,
                    "status_counts": {
                        "covered": 0,
                        "missing_outcome": 0,
                        "missing_thesis": 0,
                        "missing_weight": 0,
                    },
                    "weight_by_status": {
                        "covered": "0.0000",
                        "missing_outcome": "0.0000",
                        "missing_thesis": "0.0000",
                        "missing_weight": "0.0000",
                    },
                    "cash_weight": None,
                    "coverage_ratio_by_weight": None,
                    "positions": [],
                }
            )
        if sql.startswith("-- frontend portfolio concentration exposure lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2026-05-20",
                    "position_weight_total": "0.0000",
                    "sector_exposures": [],
                    "theme_exposures": [],
                    "unclassified_weight": "0.0000",
                    "unclassified_symbols": [],
                }
            )
        if sql.startswith("-- frontend latest portfolio snapshot date lookup"):
            return ""
        return super().execute_scalar(sql)


class ConcentratedPortfolioCoverageExecutor(FakeLiveExecutor):
    def execute_scalar(self, sql: str) -> str:
        if sql.startswith("-- frontend portfolio concentration exposure lookup"):
            return json.dumps(
                {
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2024-11-01",
                    "position_weight_total": "0.0800",
                    "sector_exposures": [
                        {
                            "exposure_key": "TECHNOLOGY",
                            "exposure_name": "Technology",
                            "exposure_weight": "0.5000",
                            "position_count": 1,
                            "symbols": ["AAPL"],
                        }
                    ],
                    "theme_exposures": [
                        {
                            "exposure_key": "AI_SEMICONDUCTOR_CYCLE",
                            "exposure_name": "AI Semiconductor Cycle",
                            "exposure_weight": "0.4500",
                            "position_count": 1,
                            "symbols": ["AAPL"],
                        }
                    ],
                    "unclassified_weight": "0.0000",
                    "unclassified_symbols": [],
                }
            )
        return super().execute_scalar(sql)


class LatestPortfolioCoverageExecutor(FakeLiveExecutor):
    def __init__(self) -> None:
        super().__init__()
        self.coverage_lookup_count = 0

    def execute_scalar(self, sql: str) -> str:
        if sql.startswith("-- frontend latest portfolio snapshot date lookup"):
            self.scalar_sql.append(sql)
            return "2026-05-19"
        if sql.startswith("-- portfolio outcome coverage report"):
            self.scalar_sql.append(sql)
            self.coverage_lookup_count += 1
            if self.coverage_lookup_count == 1:
                return json.dumps(
                    {
                        "portfolio_id": None,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2026-05-20",
                        "measurement_end_date": "2026-06-20",
                        "position_count": 0,
                        "status_counts": {
                            "covered": 0,
                            "missing_outcome": 0,
                            "missing_thesis": 0,
                            "missing_weight": 0,
                        },
                        "weight_by_status": {
                            "covered": "0.0000",
                            "missing_outcome": "0.0000",
                            "missing_thesis": "0.0000",
                            "missing_weight": "0.0000",
                        },
                        "cash_weight": None,
                        "coverage_ratio_by_weight": None,
                        "positions": [],
                    }
                )
            return json.dumps(
                {
                    "portfolio_id": 3001,
                    "portfolio_name": "Long Term Paper",
                    "snapshot_date": "2026-05-19",
                    "measurement_end_date": "2026-06-20",
                    "position_count": 1,
                    "status_counts": {
                        "covered": 1,
                        "missing_outcome": 0,
                        "missing_thesis": 0,
                        "missing_weight": 0,
                    },
                    "weight_by_status": {
                        "covered": "0.5000",
                        "missing_outcome": "0.0000",
                        "missing_thesis": "0.0000",
                        "missing_weight": "0.0000",
                    },
                    "cash_weight": "0.5000",
                    "coverage_ratio_by_weight": "1.0000",
                    "positions": [
                        {
                            "symbol": "SPY",
                            "instrument_id": 501,
                            "coverage_status": "covered",
                            "weight": "0.5000",
                            "market_value": "5000.00",
                            "linked_thesis_id": 7001,
                            "thesis_title": "SPY thesis",
                            "outcome_id": 8101,
                            "outcome_status": "working",
                            "success_grade": "pass",
                        },
                    ],
                }
            )
        return super().execute_scalar(sql)


class FrontendLiveAdapterTests(unittest.TestCase):
    def assertValuationTargetRangeQuality(
        self,
        target_range: dict[str, object],
        *,
        expected_status: str,
        expected_method_count: int = 4,
        expected_missing_methods: list[str] | None = None,
    ) -> None:
        self.assertEqual(target_range["status"], "available")
        self.assertEqual(target_range["method_count"], expected_method_count)
        self.assertEqual(target_range["order_boundary"], "read_only_no_order")
        quality = target_range["valuation_quality"]  # type: ignore[index]
        self.assertEqual(quality["status"], expected_status)
        self.assertEqual(quality["method_coverage"], expected_method_count)
        self.assertEqual(quality["expected_method_count"], 4)
        self.assertEqual(quality["missing_methods"], expected_missing_methods or [])
        self.assertEqual(quality["order_boundary"], "read_only_no_order")

        methods = target_range["methods"]  # type: ignore[index]
        self.assertEqual(len(methods), expected_method_count)
        for method in methods:
            self.assertIn("evidence_summary", method)
            self.assertIn("목표가", method["evidence_summary"])
            self.assertIn("assumption_items", method)
            self.assertGreaterEqual(len(method["assumption_items"]), 1)
            self.assertIn("sensitivity_cases", method)
            self.assertEqual([case["case_key"] for case in method["sensitivity_cases"]], ["bear", "base", "bull"])
            self.assertIn("forecast_evidence", method)
            self.assertIn(method["forecast_evidence"]["status"], {"available", "unavailable"})
            self.assertIn("data_quality", method)
            self.assertIn(method["data_quality"]["status"], {"strong", "usable", "limited"})
            self.assertIn("limitations", method)
            self.assertGreaterEqual(len(method["limitations"]), 1)

    def test_financial_statement_model_explains_source_data_blocker(self) -> None:
        payload = _build_financial_statement_model_payload(
            {
                "statement_scope": "annual",
                "metric_count": 0,
                "computed_metric_count": 0,
                "source_data_blocker": {
                    "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                    "source_pipeline": "financial_period_source_linkage",
                    "source_run_id": 1503,
                    "status": "failed",
                    "observed_at": "2026-05-26T13:00:00+00:00",
                    "error_summary": "SEC companyfacts payload does not contain facts.us-gaap",
                },
            },
            symbol="EROK",
            as_of_date="2026-05-26",
        )

        self.assertEqual(payload["status"], "unavailable")
        self.assertEqual(payload["source_data_blocker"]["blocker_code"], "sec_companyfacts_missing_us_gaap_facts")
        self.assertEqual(payload["source_data_blocker"]["source_run_id"], "pipeline-run-1503")
        self.assertIn("SEC companyfacts에 us-gaap 재무 facts가 없어", payload["summary"])
        self.assertEqual(payload["order_boundary"], "read_only_no_order")

        etf_payload = _build_financial_statement_model_payload(
            {
                "statement_scope": "annual",
                "metric_count": 0,
                "computed_metric_count": 0,
                "source_data_blocker": {
                    "blocker_code": "fund_company_financial_model_not_applicable",
                    "source_pipeline": "ref.instrument",
                    "status": "not_applicable",
                },
            },
            symbol="SPY",
            as_of_date="2026-05-26",
        )
        self.assertEqual(etf_payload["source_data_blocker"]["label"], "기업 재무 모델 비적용")
        self.assertIn("펀드형 상품", etf_payload["summary"])

    def test_source_blocked_recommendation_guardrail_blocks_professional_use(self) -> None:
        financial_model = _build_financial_statement_model_payload(
            {
                "statement_scope": "annual",
                "metric_count": 0,
                "computed_metric_count": 0,
                "source_data_blocker": {
                    "blocker_code": "sec_companyfacts_missing_us_gaap_facts",
                    "source_pipeline": "financial_period_source_linkage",
                    "source_run_id": 1503,
                    "status": "failed",
                    "observed_at": "2026-05-26T13:00:00+00:00",
                    "error_summary": "SEC companyfacts payload does not contain facts.us-gaap",
                },
            },
            symbol="EROK",
            as_of_date="2026-05-26",
        )
        source_guardrail = _build_professional_source_guardrail_payload(
            financial_statement_model=financial_model,
            fund_instrument_analysis=None,
        )
        self.assertTrue(source_guardrail["blocked"])
        self.assertFalse(source_guardrail["professional_decision_use_allowed"])
        self.assertFalse(source_guardrail["paper_validation_input_allowed"])
        self.assertEqual(source_guardrail["status"], "blocked_by_professional_source_data")
        self.assertEqual(source_guardrail["order_boundary"], "read_only_no_order")

        score_components = [
            {
                "component": "cycle_score",
                "value": 0.41,
                "weight": 0.45,
                "evidence_id": "event-101",
                "provenance": {"source_type": "event_or_ai_evidence"},
            },
            {
                "component": "rank_score",
                "value": 0.30,
                "weight": 0.15,
                "evidence_id": "universe-rank-erok-2026-05-26-1",
                "provenance": {
                    "source_type": "strategy_universe_rank",
                    "rank_position": 12,
                    "source_run_id": 9301,
                },
            },
        ]
        outcome = {"measurement_end_date": "2026-06-20", "label": "inline", "alpha": 0.0}
        evidence_review = _build_recommendation_evidence_review_payload(
            score_components=score_components,
            linked_thesis_id=8,
            outcome=outcome,
            professional_source_guardrail=source_guardrail,
        )
        self.assertEqual(evidence_review["quality_status"], "blocked")
        self.assertTrue(evidence_review["summary"]["professional_source_blocked"])
        self.assertEqual(evidence_review["summary"]["blocked_count"], 1)
        self.assertEqual(evidence_review["gates"][4]["gate_key"], "professional_source_data")
        self.assertEqual(evidence_review["gates"][4]["status"], "blocked")

        waterfall = _build_recommendation_professional_decision_waterfall_payload(
            score_components=score_components,
            equity_research=None,
            industry_competitive_position=None,
            financial_statement_model=financial_model,
            valuation_target_range={"status": "unavailable", "method_count": 0},
            linked_thesis_id=8,
            evidence_trace={
                "direct_news_or_ai": {
                    "status": "linked",
                    "impact_direction": "risk_review",
                    "impact_strength": 0.62,
                },
                "macro_flow": {"status": "missing", "propagated_impact_count": 0},
                "holding_review": {"status": "not_in_portfolio"},
            },
            evidence_review=evidence_review,
            professional_source_guardrail=source_guardrail,
            outcome=outcome,
            symbol="EROK",
            as_of_date="2026-05-26",
            recommendation="exclude",
            score=0.3486,
        )
        self.assertEqual(waterfall["status"], "source_data_blocked")
        self.assertFalse(waterfall["paper_validation_input_allowed"])
        self.assertFalse(waterfall["automatic_order_allowed"])
        self.assertFalse(waterfall["broker_submit_allowed"])
        self.assertEqual(waterfall["order_boundary"], "read_only_no_order")
        step_by_key = {step["step_key"]: step for step in waterfall["steps"]}
        self.assertEqual(step_by_key["source_data_guardrail"]["tone"], "blocked")
        self.assertEqual(step_by_key["financial_quality"]["tone"], "blocked")
        self.assertEqual(step_by_key["paper_validation"]["tone"], "blocked")
        self.assertIn("지원되는 정기 공시", waterfall["summary"])

        audit = _build_recommendation_professional_evidence_audit_payload(
            recommendation_id="recommendation-67",
            symbol="EROK",
            as_of_date="2026-05-26",
            recommendation="exclude",
            score=0.3486,
            score_components=score_components,
            equity_research=None,
            industry_competitive_position=None,
            financial_statement_model=financial_model,
            valuation_target_range={"status": "unavailable", "method_count": 0},
            fund_instrument_analysis=None,
            linked_thesis_id=8,
            evidence_trace={
                "direct_news_or_ai": {
                    "status": "linked",
                    "impact_direction": "risk_review",
                    "impact_strength": 0.62,
                },
                "macro_flow": {"status": "missing", "propagated_impact_count": 0},
                "holding_review": {"status": "not_in_portfolio"},
            },
            evidence_review=evidence_review,
            professional_source_guardrail=source_guardrail,
            professional_decision_waterfall=waterfall,
            outcome=outcome,
        )
        self.assertEqual(audit["status"], "source_blocked")
        self.assertTrue(audit["source_blocker"]["blocked"])
        self.assertEqual(audit["paper_validation_status"], "blocked_source")
        self.assertFalse(audit["paper_validation_input_allowed"])
        self.assertFalse(audit["automatic_weight_change_allowed"])
        layer_status = {layer["key"]: layer["status"] for layer in audit["layer_checks"]}
        self.assertEqual(layer_status["financial_metric_normalized"], "blocked")
        self.assertEqual(layer_status["paper_validation"], "blocked")
        self.assertEqual(audit["order_boundary"], "read_only_no_order")

    def test_fund_instrument_analysis_payload_preserves_fund_boundaries(self) -> None:
        payload = _build_fund_instrument_analysis_payload(
            {
                "status": "available",
                "analysis_type": "fund_or_etf",
                "symbol": "SPY",
                "summary": "SPY는 보유종목 구성으로 판단한다.",
                "benchmark_code": "SPY",
                "benchmark_source": "ssga_spdr_spy_daily_holdings",
                "source_type": "provider_file",
                "source_as_of_date": "2026-05-26",
                "holding_count": 503,
                "holdings_coverage_weight": 0.9983,
                "average_holding_confidence": 0.9,
                "top_holdings": [
                    {
                        "symbol": "AAPL",
                        "name": "Apple Inc.",
                        "target_weight": 0.07,
                        "confidence": 0.9,
                        "rationale": "provider holding",
                    }
                ],
                "portfolio_role": {
                    "portfolio_name": "Long Term Paper",
                    "current_weight": 0.0,
                    "recommended_weight": 0.04,
                    "role": "broad_market_or_fund_exposure",
                    "rationale": "portfolio exposure",
                },
                "tracking_error": {
                    "status": "tracking_difference_collected",
                    "value": None,
                    "metric_type": "tracking_difference",
                    "tracking_difference_value": -0.0021,
                    "source_name": "ssga_spdr_product_page",
                    "source_as_of_date": "2026-04-30",
                    "source_url": "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
                    "measurement_window": "1 Year",
                    "measurement_basis": "nav_total_return_before_tax",
                    "benchmark_name": "S&P 500 Index",
                    "fund_return": 0.3084,
                    "benchmark_return": 0.3105,
                    "summary": "tracking difference only",
                },
                "expense_ratio": {
                    "status": "collected",
                    "value": 0.000945,
                    "source_name": "ssga_spdr_product_page",
                    "source_as_of_date": "2026-05-26",
                    "source_url": "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
                    "summary": "official source",
                },
                "liquidity": {
                    "status": "collected",
                    "source_name": "market.daily_price_bar",
                    "source_as_of_date": "2026-05-26",
                    "observation_count": 60,
                    "latest_volume": 70420000,
                    "average_daily_volume": 71234567,
                    "average_daily_dollar_volume": 42000000000,
                    "summary": "거래량 수집분으로 계산했다.",
                },
                "nav_premium_discount": {
                    "status": "collected",
                    "nav_per_share": 745.571145,
                    "nav_as_of_date": "2026-05-22",
                    "bid_ask_midpoint": 745.60,
                    "closing_price": 745.64,
                    "market_price_as_of_date": "2026-05-22",
                    "premium_discount_to_nav": 0.0,
                    "premium_discount_as_of_date": "2026-05-22",
                    "source_name": "ssga_spdr_product_page",
                    "source_url": "https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy",
                    "summary": "NAV와 프리미엄·디스카운트를 공식 원천에서 수집했다.",
                },
                "limitations": ["no company financials"],
            }
        )

        self.assertIsNotNone(payload)
        assert payload is not None
        self.assertEqual(payload["symbol"], "SPY")
        self.assertEqual(payload["benchmark_source"], "ssga_spdr_spy_daily_holdings")
        self.assertEqual(payload["top_holdings"][0]["symbol"], "AAPL")
        self.assertEqual(payload["tracking_error"]["status"], "tracking_difference_collected")
        self.assertEqual(payload["tracking_error"]["metric_type"], "tracking_difference")
        self.assertEqual(payload["tracking_error"]["tracking_difference_value"], -0.0021)
        self.assertEqual(payload["tracking_error"]["measurement_window"], "1 Year")
        self.assertEqual(payload["tracking_error"]["benchmark_name"], "S&P 500 Index")
        self.assertEqual(payload["tracking_error"]["fund_return"], 0.3084)
        self.assertEqual(payload["tracking_error"]["benchmark_return"], 0.3105)
        self.assertEqual(payload["expense_ratio"]["status"], "collected")
        self.assertEqual(payload["expense_ratio"]["value"], 0.000945)
        self.assertEqual(payload["expense_ratio"]["source_name"], "ssga_spdr_product_page")
        self.assertEqual(payload["expense_ratio"]["source_as_of_date"], "2026-05-26")
        self.assertEqual(payload["liquidity"]["status"], "collected")
        self.assertEqual(payload["liquidity"]["source_name"], "market.daily_price_bar")
        self.assertEqual(payload["liquidity"]["observation_count"], 60)
        self.assertEqual(payload["nav_premium_discount"]["status"], "collected")
        self.assertEqual(payload["nav_premium_discount"]["nav_per_share"], 745.571145)
        self.assertEqual(payload["nav_premium_discount"]["closing_price"], 745.64)
        self.assertEqual(payload["nav_premium_discount"]["premium_discount_to_nav"], 0.0)
        self.assertEqual(payload["nav_premium_discount"]["source_name"], "ssga_spdr_product_page")
        self.assertIn("NAV", payload["nav_premium_discount"]["summary"])
        self.assertEqual(payload["score_policy"], "recommendation_weights_unchanged")
        self.assertFalse(payload["automatic_order_allowed"])
        self.assertFalse(payload["broker_submit_allowed"])
        self.assertEqual(payload["order_boundary"], "read_only_no_order")

    def test_live_dashboard_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/dashboard/today",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["run_status"]["daily_automation"], "succeeded")
        self.assertEqual(payload["data"]["run_status"]["latest_run_id"], "pipeline-run-9101")
        self.assertEqual(payload["data"]["run_status"]["scheduler"], "not_installed")
        self.assertFalse(payload["data"]["run_status"]["holiday_skip"]["would_skip_today"])
        self.assertEqual(payload["data"]["attention_summary"]["open_ticket_count"], 1)
        self.assertEqual(payload["data"]["attention_summary"]["critical_blind_spot_count"], 1)
        self.assertEqual(payload["data"]["top_actions"][0]["rank"], 1)
        self.assertEqual(payload["data"]["top_actions"][0]["symbol"], "BABA")
        self.assertEqual(payload["data"]["top_actions"][0]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["latest_metrics"]["covered_weight"], 0.05)
        self.assertEqual(payload["data"]["latest_metrics"]["missing_thesis_weight"], 0.03)
        self.assertEqual(payload["data"]["latest_metrics"]["cash_weight"], 0.92)
        self.assertEqual(payload["data"]["latest_metrics"]["weight_coverage_ratio"], 0.625)
        self.assertEqual(
            payload["links"]["portfolio_coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_dashboard_response_uses_profile_scheduler_status_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "profile-scheduler-status.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "operating_data_profile_scheduler_status",
                        "status": "installed",
                        "install_status": "installed",
                        "scheduler_type": "systemd",
                        "timer_count": 1,
                        "active_timer_count": 1,
                        "generated_at": "2026-05-21T00:40:00Z",
                        "timers": [],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/dashboard/today",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        self.assertEqual(payload["data"]["run_status"]["scheduler"], "installed")

    def test_live_data_health_response_matches_frontend_contract_shape(self) -> None:
        with patch.dict(os.environ, {"STOCKANALYSIS_CYCLE_AI_QUALITY_AUDIT_REPORT": ""}):
            payload = resolve_live_frontend_response(
                "/api/data-health",
                config=type("Config", (), {"psql_command": "psql"})(),
                executor=FakeLiveExecutor(),
                generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["overall_status"], "attention_required")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["latest_run_id"], "pipeline-run-9101")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["finished_at"], "2024-11-01T23:30:00Z")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["job_id"], "portfolio-remediation-daily")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["cadence"], "daily")
        self.assertEqual(payload["data"]["pipeline_runs"][0]["health_status"], "ok")
        self.assertEqual(
            payload["data"]["pipeline_runs"][0]["artifact_policy"],
            "stdout_json_stderr_log_and_summary_link",
        )
        self.assertEqual(payload["data"]["scheduler"]["install_status"], "not_installed")
        self.assertEqual(
            payload["data"]["scheduler"]["runtime_env_readiness"],
            "template_rendered_placeholder_pending",
        )
        self.assertEqual(payload["data"]["scheduler"]["activation"]["status"], "not_configured")
        self.assertEqual(payload["data"]["scheduler"]["activation"]["source"], "not_configured")
        production_api = payload["data"]["production_api_server"]
        self.assertEqual(production_api["status"], "missing_runtime_evidence")
        self.assertTrue(production_api["attention_required"])
        self.assertEqual(production_api["connection_boundary"], "injected_executor")
        self.assertIn("production_api_server", payload["data"]["open_gates"])
        auth_rbac = payload["data"]["auth_rbac"]
        self.assertEqual(auth_rbac["status"], "missing_rbac_evidence")
        self.assertTrue(auth_rbac["attention_required"])
        self.assertFalse(auth_rbac["write_methods_allowed"])
        self.assertFalse(auth_rbac["broker_submit_allowed"])
        self.assertEqual(auth_rbac["order_boundary"], "read_only_no_order")
        self.assertIn("auth_rbac", payload["data"]["open_gates"])
        alert_destination = payload["data"]["alert_destination"]
        self.assertEqual(alert_destination["status"], "missing_destination")
        self.assertTrue(alert_destination["attention_required"])
        self.assertIn("alert_destination", payload["data"]["open_gates"])
        self.assertEqual(payload["data"]["freshness"][0]["dataset"], "market.daily_price_bar")
        self.assertEqual(payload["data"]["freshness"][0]["latest_observation_date"], "2024-12-02")
        self.assertEqual(payload["data"]["provider_budget"]["status"], "not_configured")
        self.assertEqual(payload["data"]["provider_budget"]["provider"], "alpha_vantage")
        price_freshness = payload["data"]["active_recommendation_price_freshness"]
        self.assertEqual(price_freshness["status"], "stale_prices")
        self.assertTrue(price_freshness["attention_required"])
        self.assertEqual(price_freshness["active_symbol_count"], 2)
        self.assertEqual(price_freshness["stale_symbol_count"], 1)
        self.assertEqual(price_freshness["stale_symbols"][0]["symbol"], "QUBT")
        self.assertEqual(price_freshness["stale_symbols"][0]["instrument_id"], "instrument-7002")
        self.assertFalse(price_freshness["automatic_order_allowed"])
        self.assertEqual(price_freshness["order_boundary"], "read_only_no_order")
        self.assertIn("active_recommendation_price_freshness_attention", payload["data"]["open_gates"])
        self.assertEqual(payload["data"]["manual_local_ingest_smoke"]["status"], "not_configured")
        self.assertEqual(payload["data"]["manual_local_ingest_smoke"]["source"], "not_configured")
        self.assertEqual(payload["data"]["local_ingest_worker"]["status"], "not_configured")
        self.assertEqual(payload["data"]["local_ingest_worker"]["source"], "not_configured")
        artifact_runner = payload["data"]["data_operations_artifact_runner"]
        self.assertEqual(artifact_runner["status"], "runner_evidence_available")
        self.assertEqual(artifact_runner["job_count"], 1)
        self.assertEqual(artifact_runner["artifact_policy_count"], 1)
        self.assertEqual(artifact_runner["latest_run_count"], 1)
        self.assertFalse(artifact_runner["attention_required"])
        self.assertNotIn("data_operations_artifact_runner", payload["data"]["open_gates"])
        self.assertEqual(payload["data"]["cycle_ai_quality_audit"]["status"], "not_configured")
        self.assertEqual(payload["data"]["cycle_ai_quality_audit"]["source"], "not_configured")
        news_eval = payload["data"]["news_ai_eval_quality"]
        self.assertEqual(news_eval["status"], "passed")
        self.assertEqual(news_eval["eval_run_id"], "eval-run-72")
        self.assertEqual(news_eval["eval_name"], "news_ai_extraction_quality")
        self.assertEqual(news_eval["dataset_version"], "news-ai-eval-v1")
        self.assertTrue(news_eval["overall_pass"])
        self.assertEqual(news_eval["case_count"], 5)
        self.assertEqual(news_eval["failed_case_count"], 0)
        self.assertEqual(news_eval["theme_precision"], 1.0)
        self.assertEqual(news_eval["direct_ticker_grounding_precision"], 1.0)
        self.assertEqual(news_eval["macro_only_false_ticker_count"], 0)
        self.assertEqual(news_eval["quantum_energy_misclassification_count"], 0)
        self.assertEqual(news_eval["case_results"][0]["accepted_theme_codes"], ["QUANTUM_COMPUTING_POLICY"])
        self.assertNotIn("news_ai_eval_quality_attention", payload["data"]["open_gates"])
        live_ai = payload["data"]["live_ai_invocation_health"]
        self.assertEqual(live_ai["status"], "healthy")
        self.assertFalse(live_ai["attention_required"])
        self.assertEqual(live_ai["recent_success_count"], 12)
        self.assertNotIn("live_ai_invocation_health_attention", payload["data"]["open_gates"])
        drift_quality = payload["data"]["benchmark_drift_quality"]
        self.assertEqual(drift_quality["status"], "partial_composition")
        self.assertEqual(drift_quality["guardrail_eval_run_id"], "eval-run-22")
        self.assertEqual(drift_quality["benchmark_code"], "SPY")
        self.assertEqual(drift_quality["benchmark_source"], "operator_spy_holdings_2026_05_25")
        self.assertEqual(drift_quality["composition_coverage_weight"], 0.215)
        self.assertEqual(drift_quality["active_share"], 0.3925)
        self.assertEqual(drift_quality["outlier_positions"][0]["symbol"], "MSFT")
        self.assertEqual(drift_quality["review_candidate_count"], 1)
        self.assertEqual(drift_quality["review_decision_counts"]["reduce_watch"], 1)
        self.assertEqual(drift_quality["outlier_decisions"][0]["symbol"], "MSFT")
        self.assertEqual(drift_quality["outlier_decisions"][0]["review_decision"], "reduce_watch")
        self.assertEqual(drift_quality["outlier_decisions"][0]["decision_label"], "비중 축소 검토")
        self.assertEqual(
            drift_quality["outlier_decisions"][0]["source_evidence"]["benchmark_source"],
            "operator_spy_holdings_2026_05_25",
        )

        self.assertFalse(drift_quality["automatic_order_allowed"])
        self.assertFalse(drift_quality["broker_submit_allowed"])
        self.assertEqual(drift_quality["order_boundary"], "read_only_no_order")
        self.assertTrue(drift_quality["attention_required"])
        self.assertEqual(drift_quality["managed_review_status"], "source_or_guardrail_gap")
        self.assertIn("benchmark_drift_quality_attention", payload["data"]["open_gates"])
        review_history = payload["data"]["portfolio_review_decision_history"]
        self.assertEqual(review_history["status"], "loaded")
        self.assertEqual(review_history["eval_run_id"], "eval-run-52")
        self.assertEqual(review_history["decision_status"], "review_required")
        self.assertEqual(review_history["decision_count"], 2)
        self.assertEqual(review_history["benchmark_decision_count"], 1)
        self.assertEqual(review_history["position_sizing_decision_count"], 1)
        self.assertEqual(review_history["top_decision"]["symbol"], "MSFT")
        self.assertEqual(review_history["latest_decisions"][0]["decision_label"], "비중 축소 검토")
        self.assertFalse(review_history["guardrails"]["automatic_rebalance_allowed"])
        self.assertFalse(review_history["guardrails"]["broker_submit_allowed"])
        self.assertEqual(review_history["guardrails"]["order_boundary"], "read_only_no_order")
        self.assertFalse(review_history["attention_required"])
        self.assertEqual(review_history["managed_review_status"], "waiting_for_outcome_window")
        self.assertNotIn("portfolio_review_decision_history_attention", payload["data"]["open_gates"])
        review_feedback = payload["data"]["portfolio_review_decision_feedback"]
        self.assertEqual(review_feedback["status"], "loaded")
        self.assertEqual(review_feedback["eval_run_id"], "eval-run-53")
        self.assertEqual(review_feedback["source_history_eval_run_id"], "eval-run-52")
        self.assertEqual(review_feedback["feedback_status"], "too_early")
        self.assertEqual(review_feedback["decision_count"], 1)
        self.assertEqual(review_feedback["too_early_count"], 1)
        self.assertEqual(review_feedback["top_feedback"]["symbol"], "MSFT")
        self.assertEqual(review_feedback["top_feedback"]["feedback_status"], "too_early")
        self.assertFalse(review_feedback["guardrails"]["automatic_order_allowed"])
        self.assertFalse(review_feedback["guardrails"]["broker_submit_allowed"])
        self.assertEqual(review_feedback["guardrails"]["order_boundary"], "read_only_no_order")
        review_calibration = payload["data"]["portfolio_review_feedback_calibration"]
        self.assertEqual(review_calibration["status"], "loaded")
        self.assertEqual(review_calibration["eval_run_id"], "eval-run-54")
        self.assertEqual(review_calibration["calibration_status"], "insufficient_history")
        self.assertEqual(review_calibration["maturity_status"], "waiting_for_outcome_window")
        self.assertEqual(review_calibration["feedback_run_count"], 1)
        self.assertEqual(review_calibration["min_feedback_runs"], 3)
        self.assertEqual(review_calibration["feedback_run_gap"], 2)
        self.assertEqual(review_calibration["decision_count"], 1)
        self.assertEqual(review_calibration["min_mature_decisions"], 10)
        self.assertEqual(review_calibration["mature_decision_gap"], 10)
        self.assertEqual(review_calibration["estimated_maturity_date"], "2026-06-24")
        self.assertEqual(review_calibration["days_until_maturity"], 28)
        self.assertFalse(review_calibration["attention_required"])
        self.assertTrue(review_calibration["managed_wait"])
        self.assertEqual(review_calibration["managed_gate_status"], "managed_wait_until_outcome_window")
        self.assertIn("관리된 대기", review_calibration["managed_gate_reason"])
        self.assertTrue(review_calibration["weight_review_blocked"])
        self.assertIn("최소 30일 관찰 기간", review_calibration["weight_review_block_reason"])
        self.assertEqual(review_calibration["family_summaries"][0]["decision_family"], "benchmark_drift")
        self.assertEqual(review_calibration["symbol_summaries"][0]["symbol"], "MSFT")
        self.assertFalse(review_calibration["guardrails"]["automatic_order_allowed"])
        self.assertFalse(review_calibration["guardrails"]["broker_submit_allowed"])
        self.assertEqual(review_calibration["guardrails"]["order_boundary"], "read_only_no_order")
        self.assertNotIn("portfolio_review_feedback_calibration_attention", payload["data"]["open_gates"])
        review_cadence = payload["data"]["portfolio_review_feedback_cadence"]
        self.assertEqual(review_cadence["status"], "loaded")
        self.assertEqual(review_cadence["eval_run_id"], "eval-run-55")
        self.assertEqual(review_cadence["cadence_status"], "wait_for_outcome_window")
        self.assertEqual(review_cadence["action_type"], "wait")
        self.assertFalse(review_cadence["should_run_now"])
        self.assertTrue(review_cadence["should_wait"])
        self.assertEqual(review_cadence["history"]["eval_run_id"], "eval-run-52")
        self.assertEqual(review_cadence["feedback"]["eval_run_id"], "eval-run-53")
        self.assertEqual(review_cadence["calibration"]["eval_run_id"], "eval-run-54")
        self.assertEqual(review_cadence["evidence"]["history_age_days"], 2)
        self.assertFalse(review_cadence["automatic_order_allowed"])
        self.assertFalse(review_cadence["broker_submit_allowed"])
        self.assertEqual(review_cadence["order_boundary"], "read_only_no_order")
        action_router = payload["data"]["portfolio_review_feedback_action_router"]
        self.assertEqual(action_router["status"], "loaded")
        self.assertEqual(action_router["eval_run_id"], "eval-run-56")
        self.assertEqual(action_router["source_cadence_eval_run_id"], "eval-run-55")
        self.assertEqual(action_router["route_action"], "no_op")
        self.assertEqual(action_router["action_status"], "no_op_wait_for_outcome_window")
        self.assertFalse(action_router["child_runner"]["executed"])
        self.assertEqual(action_router["child_runner"]["status"], "not_run")
        self.assertEqual(action_router["history_eval_run_id"], "eval-run-52")
        self.assertEqual(action_router["feedback_eval_run_id"], "eval-run-53")
        self.assertEqual(action_router["calibration_eval_run_id"], "eval-run-54")
        self.assertFalse(action_router["automatic_order_allowed"])
        self.assertFalse(action_router["broker_submit_allowed"])
        self.assertEqual(action_router["order_boundary"], "read_only_no_order")
        outcome_calibration = payload["data"]["recommendation_outcome_calibration"]
        self.assertEqual(outcome_calibration["status"], "collect_more_outcomes_keep_weights")
        self.assertEqual(outcome_calibration["eval_run_id"], "eval-run-31")
        self.assertEqual(outcome_calibration["horizon_days"], [30, 90])
        self.assertEqual(outcome_calibration["outcome_count"], 4)
        self.assertEqual(outcome_calibration["outcome_coverage_rate"], 0.333333)
        self.assertEqual(outcome_calibration["ready_for_backfill_count"], 2)
        self.assertEqual(outcome_calibration["missing_reason_counts"]["ready_for_backfill"], 2)
        self.assertFalse(outcome_calibration["recommendation_scoring_mutated"])
        self.assertFalse(outcome_calibration["automatic_order_allowed"])
        self.assertEqual(outcome_calibration["order_boundary"], "read_only_no_order")
        outcome_maturity = payload["data"]["recommendation_outcome_maturity"]
        self.assertEqual(outcome_maturity["status"], "not_due")
        self.assertEqual(outcome_maturity["source_calibration_eval_run_id"], "eval-run-31")
        self.assertEqual(outcome_maturity["horizon_days"], [30, 90])
        self.assertEqual(outcome_maturity["next_due_date"], "2026-06-01")
        self.assertEqual(outcome_maturity["next_due_count"], 3)
        self.assertEqual(outcome_maturity["due_today_count"], 1)
        self.assertEqual(outcome_maturity["overdue_count"], 1)
        self.assertEqual(outcome_maturity["price_gap_count"], 1)
        self.assertEqual(outcome_maturity["examples"][0]["recommendation_id"], "recommendation-147")
        self.assertEqual(outcome_maturity["cadence_action"]["status"], "wait_until_next_due_date")
        self.assertEqual(outcome_maturity["cadence_action"]["wait_until"], "2026-06-01")
        self.assertFalse(outcome_maturity["cadence_action"]["should_run_now"])
        self.assertTrue(outcome_maturity["cadence_action"]["should_wait"])
        self.assertIn("--as-of-date 2026-06-01", outcome_maturity["cadence_action"]["command"])
        self.assertTrue(outcome_maturity["cadence_action"]["blocks_weight_review"])
        self.assertFalse(outcome_maturity["recommendation_scoring_mutated"])
        due_router = payload["data"]["recommendation_outcome_due_action_router"]
        self.assertEqual(due_router["status"], "loaded")
        self.assertEqual(due_router["eval_run_id"], "eval-run-71")
        self.assertEqual(due_router["source_calibration_eval_run_id"], "eval-run-31")
        self.assertEqual(due_router["route_action"], "no_op")
        self.assertEqual(due_router["action_status"], "no_op_wait_until_next_due_date")
        self.assertEqual(due_router["wait_until"], "2026-06-01")
        self.assertFalse(due_router["child_runner"]["executed"])
        self.assertFalse(due_router["automatic_weight_change_allowed"])
        self.assertFalse(due_router["broker_submit_allowed"])
        weight_review = payload["data"]["recommendation_weight_review_readiness"]
        self.assertEqual(weight_review["status"], "blocked_by_outcome_calibration_no_due_outcome_window")
        self.assertEqual(weight_review["eval_run_id"], "eval-run-41")
        self.assertEqual(weight_review["source_eval_run_id"], "eval-run-26")
        self.assertEqual(weight_review["outcome_calibration_eval_run_id"], "eval-run-27")
        self.assertEqual(weight_review["outcome_calibration_status"], "no_due_outcome_window")
        self.assertFalse(weight_review["manual_weight_review_allowed"])
        self.assertFalse(weight_review["automatic_weight_change_allowed"])
        wait_monitor = payload["data"]["outcome_maturity_wait_monitor"]
        self.assertEqual(wait_monitor["status"], "managed_wait")
        self.assertEqual(wait_monitor["recommendation_next_due_date"], "2026-06-01")
        self.assertEqual(wait_monitor["recommendation_next_due_count"], 3)
        self.assertEqual(wait_monitor["portfolio_feedback_maturity_date"], "2026-06-24")
        self.assertEqual(wait_monitor["portfolio_mature_decision_gap"], 10)
        self.assertEqual(wait_monitor["earliest_action_date"], "2026-06-01")
        self.assertTrue(wait_monitor["weight_review_blocked"])
        self.assertFalse(wait_monitor["manual_weight_review_allowed"])
        self.assertFalse(wait_monitor["automatic_weight_change_allowed"])
        self.assertFalse(wait_monitor["broker_submit_allowed"])
        self.assertEqual(wait_monitor["order_boundary"], "read_only_no_order")
        self.assertEqual(wait_monitor["wait_items"][0]["scope"], "recommendation_outcome")
        self.assertEqual(wait_monitor["wait_items"][1]["scope"], "portfolio_feedback")
        source_gaps = payload["data"]["professional_source_gap_prioritization"]
        self.assertEqual(source_gaps["status"], "source_blockers_present")
        self.assertEqual(source_gaps["gap_count"], 2)
        self.assertEqual(source_gaps["source_blocker_count"], 1)
        self.assertEqual(source_gaps["fund_not_applicable_count"], 1)
        self.assertEqual(source_gaps["guarded_source_blocked_recommendation_count"], 1)
        self.assertEqual(source_gaps["gaps"][0]["symbol"], "EROK")
        self.assertEqual(source_gaps["gaps"][0]["blocker_label"], "SEC us-gaap facts 없음")
        self.assertFalse(source_gaps["gaps"][0]["professional_decision_use_allowed"])
        self.assertTrue(source_gaps["gaps"][0]["active_recommendation_professional_use_blocked"])
        self.assertFalse(source_gaps["gaps"][0]["paper_validation_input_allowed"])
        self.assertEqual(source_gaps["gaps"][0]["source_run_id"], "pipeline-run-1503")
        self.assertEqual(
            source_gaps["gaps"][0]["raw_filing_decision"]["status"],
            "durable_exclusion_until_periodic_filing",
        )
        self.assertEqual(source_gaps["gaps"][0]["raw_filing_decision"]["eval_run_id"], "eval-run-29")
        self.assertEqual(
            source_gaps["gaps"][0]["raw_filing_decision"]["blocker_code"],
            "ipo_prospectus_without_standard_periodic_financials",
        )
        self.assertEqual(source_gaps["gaps"][0]["raw_filing_decision"]["latest_prospectus_form_type"], "424B4")
        self.assertIn("periodic filing", source_gaps["gaps"][0]["remediation_action"])
        self.assertIn("재무 지표 정규화", source_gaps["gaps"][0]["missing_layer_labels"])
        self.assertEqual(source_gaps["gaps"][1]["symbol"], "SPY")
        self.assertEqual(source_gaps["gaps"][1]["product_type"], "fund_or_etf")
        self.assertEqual(source_gaps["gaps"][1]["blocker_type"], "fund_not_applicable")
        self.assertEqual(source_gaps["gaps"][1]["blocker_label"], "기업 재무 모델 비적용")
        self.assertTrue(source_gaps["gaps"][1]["professional_decision_use_allowed"])
        self.assertFalse(source_gaps["gaps"][1]["active_recommendation_professional_use_blocked"])
        self.assertFalse(source_gaps["recommendation_scoring_mutated"])
        self.assertFalse(source_gaps["automatic_weight_change_allowed"])
        self.assertFalse(source_gaps["broker_submit_allowed"])
        self.assertFalse(source_gaps["attention_required"])
        self.assertNotIn("professional_source_gap_attention", payload["data"]["open_gates"])
        professional_depth = payload["data"]["professional_analysis_depth"]
        self.assertEqual(professional_depth["status"], "source_limited")
        self.assertEqual(professional_depth["active_candidate_count"], 2)
        self.assertEqual(professional_depth["complete_candidate_count"], 1)
        self.assertEqual(professional_depth["source_blocked_count"], 1)
        self.assertEqual(professional_depth["average_coverage_ratio"], 0.775)
        self.assertEqual(professional_depth["layer_coverage"][0]["coverage_ratio"], 0.0)
        self.assertEqual(professional_depth["layer_coverage"][1]["coverage_ratio"], 1.0)
        self.assertEqual(professional_depth["items"][0]["symbol"], "EROK")
        self.assertEqual(professional_depth["items"][0]["depth_status"], "source_blocked")
        self.assertIn("재무 지표 정규화", professional_depth["items"][0]["missing_layer_labels"])
        self.assertFalse(professional_depth["automatic_weight_change_allowed"])
        self.assertFalse(professional_depth["broker_submit_allowed"])
        self.assertEqual(professional_depth["order_boundary"], "read_only_no_order")
        professional_quality = payload["data"]["professional_analysis_quality"]
        self.assertEqual(professional_quality["status"], "managed_source_limited")
        self.assertEqual(professional_quality["active_candidate_count"], 2)
        self.assertEqual(professional_quality["complete_candidate_count"], 1)
        self.assertEqual(professional_quality["source_blocked_count"], 1)
        self.assertEqual(professional_quality["average_coverage_ratio"], 0.775)
        layer_checks = {item["layer_key"]: item for item in professional_quality["layer_checks"]}
        self.assertEqual(layer_checks["financial_metric_normalized"]["status"], "missing")
        self.assertEqual(layer_checks["valuation_snapshot"]["status"], "complete")
        self.assertEqual(layer_checks["fund_source_layers"]["status"], "complete")
        quality_checks = {item["key"]: item for item in professional_quality["quality_checks"]}
        self.assertEqual(quality_checks["source_guardrail"]["status"], "managed")
        self.assertEqual(quality_checks["weight_boundary"]["status"], "blocked")
        self.assertFalse(professional_quality["automatic_weight_change_allowed"])
        self.assertFalse(professional_quality["recommendation_scoring_mutated"])
        self.assertFalse(professional_quality["broker_submit_allowed"])
        self.assertEqual(professional_quality["order_boundary"], "read_only_no_order")
        recommendation_audit = payload["data"]["professional_recommendation_coverage_audit"]
        self.assertEqual(recommendation_audit["status"], "source_limited")
        self.assertEqual(recommendation_audit["recommendation_count"], 2)
        self.assertEqual(recommendation_audit["source_blocked_count"], 1)
        self.assertEqual(recommendation_audit["paper_validation_pending_count"], 1)
        self.assertEqual(recommendation_audit["items"][0]["recommendation_id"], "recommendation-67")
        self.assertEqual(recommendation_audit["items"][0]["symbol"], "EROK")
        self.assertEqual(recommendation_audit["items"][0]["audit_status"], "blocked_source")
        self.assertIn("재무 지표 정규화", recommendation_audit["items"][0]["missing_layer_labels"])
        self.assertEqual(recommendation_audit["items"][0]["paper_validation_status"], "missing")
        self.assertFalse(recommendation_audit["automatic_weight_change_allowed"])
        self.assertFalse(recommendation_audit["broker_submit_allowed"])
        self.assertEqual(recommendation_audit["order_boundary"], "read_only_no_order")
        professional_next = payload["data"]["professional_analysis_next_action"]
        self.assertEqual(professional_next["status"], "managed_outcome_wait")
        self.assertTrue(professional_next["managed_wait"])
        self.assertTrue(professional_next["weight_review_blocked"])
        self.assertEqual(professional_next["average_coverage_ratio"], 0.775)
        self.assertEqual(professional_next["next_symbol"], "EROK")
        self.assertFalse(professional_next["automatic_weight_change_allowed"])
        self.assertFalse(professional_next["broker_submit_allowed"])
        self.assertEqual(professional_next["order_boundary"], "read_only_no_order")
        gate_details = {item["gate_id"]: item for item in payload["data"]["open_gate_details"]}
        self.assertEqual(gate_details["auth_rbac"]["category"], "operational_blocker")
        self.assertEqual(gate_details["auth_rbac"]["severity"], "high")
        self.assertIn("쓰기/주문 차단", gate_details["auth_rbac"]["summary"])
        self.assertEqual(gate_details["benchmark_drift_quality_attention"]["category"], "investment_review")
        self.assertNotIn("portfolio_review_decision_history_attention", gate_details)
        self.assertNotIn("portfolio_review_feedback_calibration_attention", gate_details)
        self.assertNotIn("professional_source_gap_attention", gate_details)
        self.assertEqual(payload["links"]["dashboard"], "/api/dashboard/today")

    def test_data_health_overall_status_uses_final_open_gates(self) -> None:
        self.assertEqual(
            _resolve_data_health_overall_status(
                open_gates=[],
                fallback_status="attention_required",
            ),
            "healthy",
        )
        self.assertEqual(
            _resolve_data_health_overall_status(
                open_gates=["active_recommendation_price_freshness_attention"],
                fallback_status="healthy",
            ),
            "attention_required",
        )
        self.assertEqual(
            _resolve_data_health_overall_status(
                open_gates=[],
                fallback_status="unknown",
            ),
            "unknown",
        )

    def test_portfolio_review_feedback_maturity_visibility_computes_wait_until_when_missing(self) -> None:
        calibration = _build_portfolio_review_feedback_calibration_payload(
            {
                "status": "loaded",
                "as_of_date": "2026-05-27",
                "calibration_status": "insufficient_history",
                "min_feedback_runs": 3,
                "min_mature_decisions": 10,
                "feedback_run_count": 1,
                "mature_decision_count": 0,
            }
        )
        cadence = _build_portfolio_review_feedback_cadence_payload(
            {
                "status": "loaded",
                "as_of_date": "2026-05-27",
                "min_horizon_days": 30,
                "cadence_status": "wait_for_outcome_window",
                "should_wait": True,
                "wait_until": "",
                "history": {"status": "loaded", "as_of_date": "2026-05-25"},
            }
        )

        enriched = _attach_portfolio_review_feedback_maturity_visibility(calibration, cadence)

        self.assertEqual(enriched["maturity_status"], "waiting_for_outcome_window")
        self.assertEqual(enriched["estimated_maturity_date"], "2026-06-24")
        self.assertEqual(enriched["days_until_maturity"], 28)
        self.assertEqual(enriched["feedback_run_gap"], 2)
        self.assertEqual(enriched["mature_decision_gap"], 10)
        self.assertTrue(enriched["attention_required"])
        self.assertTrue(enriched["weight_review_blocked"])
        self.assertIn("2026-06-24", enriched["weight_review_block_reason"])
        managed = _apply_portfolio_review_feedback_managed_wait_policy(
            calibration=enriched,
            cadence=cadence,
            action_router={
                "action_status": "no_op_wait_for_outcome_window",
                "automatic_weight_change_allowed": False,
                "automatic_order_allowed": False,
                "broker_submit_allowed": False,
            },
        )
        self.assertFalse(managed["attention_required"])
        self.assertTrue(managed["managed_wait"])
        self.assertEqual(managed["managed_gate_status"], "managed_wait_until_outcome_window")
        self.assertTrue(managed["weight_review_blocked"])

    def test_data_operations_artifact_runner_payload_blocks_when_pipeline_evidence_missing(self) -> None:
        payload = _build_data_operations_artifact_runner_payload(
            pipeline_runs=[],
            scheduler={"profile_scheduler": {"install_status": "not_installed"}},
            manual_local_ingest_smoke={"status": "not_configured"},
            local_ingest_worker={"status": "not_configured"},
        )

        self.assertEqual(payload["status"], "missing_pipeline_evidence")
        self.assertTrue(payload["attention_required"])
        self.assertEqual(payload["job_count"], 0)
        self.assertIn("성공한 data operation run evidence", payload["next_action"])

    def test_data_operations_artifact_runner_payload_closes_when_scheduler_and_artifact_evidence_exist(self) -> None:
        payload = _build_data_operations_artifact_runner_payload(
            pipeline_runs=[
                {
                    "job_id": "news-rss-daily",
                    "artifact_policy": "stdout_json_and_stderr_log",
                    "latest_run_id": "pipeline-run-1710",
                    "health_status": "ok",
                },
                {
                    "job_id": "market-price-daily",
                    "artifact_policy": "stdout_json_and_stderr_log",
                    "latest_run_id": "pipeline-run-1664",
                    "health_status": "degraded",
                },
            ],
            scheduler={
                "latest_artifact_root": "",
                "profile_scheduler": {
                    "install_status": "installed",
                    "timer_count": 7,
                    "active_timer_count": 7,
                },
            },
            manual_local_ingest_smoke={
                "status": "passed",
                "artifact_root": "/opt/stockanalysis/artifacts/data-operations",
            },
            local_ingest_worker={"status": "completed"},
        )

        self.assertEqual(payload["status"], "operational_profile_scheduler_active")
        self.assertFalse(payload["attention_required"])
        self.assertEqual(payload["job_count"], 2)
        self.assertEqual(payload["artifact_policy_count"], 2)
        self.assertEqual(payload["latest_run_count"], 2)
        self.assertEqual(payload["degraded_count"], 1)
        self.assertEqual(payload["latest_artifact_root"], "/opt/stockanalysis/artifacts/data-operations")

    def test_production_api_server_payload_blocks_without_production_runtime_evidence(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            payload = _build_production_api_server_payload(
                config=RuntimeConfig(psql_command="psql"),
                executor=FakeLiveExecutor(),
            )

        self.assertEqual(payload["status"], "missing_runtime_evidence")
        self.assertTrue(payload["attention_required"])
        self.assertIn("runtime_profile_production", payload["missing_conditions"])
        self.assertIn("psycopg_pool_boundary", payload["missing_conditions"])

    def test_production_api_server_payload_closes_with_production_live_pool_runtime(self) -> None:
        pool_executor = type("PsycopgPoolExecutor", (), {})()
        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE": "production",
                "STOCKANALYSIS_FRONTEND_API_SOURCE": "live",
                "STOCKANALYSIS_FRONTEND_API_AUTH_MODE": "read-token",
                "STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "secret",
                "STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN": "https://stockanalysis.local",
                "STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS": "30",
            },
            clear=True,
        ):
            payload = _build_production_api_server_payload(
                config=RuntimeConfig(database_url="postgresql://example.invalid/db"),
                executor=pool_executor,
            )

        self.assertEqual(payload["status"], "production_ready")
        self.assertFalse(payload["attention_required"])
        self.assertEqual(payload["runtime_profile"], "production")
        self.assertEqual(payload["source_mode"], "live")
        self.assertEqual(payload["auth_mode"], "read-token")
        self.assertTrue(payload["read_token_configured"])
        self.assertTrue(payload["allowed_origin_configured"])
        self.assertTrue(payload["database_configured"])
        self.assertEqual(payload["connection_boundary"], "psycopg_pool")
        self.assertEqual(payload["missing_conditions"], [])

    def test_auth_rbac_payload_blocks_without_production_readonly_boundary(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            payload = _build_auth_rbac_payload(
                production_api_server={"status": "missing_runtime_evidence"}
            )

        self.assertEqual(payload["status"], "missing_rbac_evidence")
        self.assertTrue(payload["attention_required"])
        self.assertIn("production_api_ready", payload["missing_conditions"])
        self.assertIn("bearer_read_token", payload["missing_conditions"])
        self.assertFalse(payload["write_methods_allowed"])
        self.assertFalse(payload["broker_submit_allowed"])
        self.assertEqual(payload["order_boundary"], "read_only_no_order")

    def test_auth_rbac_payload_closes_with_readonly_role_boundary(self) -> None:
        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_FRONTEND_API_AUTH_MODE": "read-token",
                "STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "secret",
                "STOCKANALYSIS_FRONTEND_API_READ_ROLE": "analyst",
            },
            clear=True,
        ):
            payload = _build_auth_rbac_payload(
                production_api_server={"status": "production_ready"}
            )

        self.assertEqual(payload["status"], "read_only_rbac_ready")
        self.assertFalse(payload["attention_required"])
        self.assertEqual(payload["mode"], "read-only-token")
        self.assertEqual(payload["read_role"], "analyst")
        self.assertEqual(payload["missing_conditions"], [])
        self.assertEqual(payload["protected_paths"], ["/__endpoints", "/api/*"])
        self.assertEqual(payload["allowed_methods"], ["GET", "HEAD", "OPTIONS"])

    def test_alert_destination_payload_blocks_when_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            payload = _build_alert_destination_payload(generated_at="2026-05-27T00:00:00Z")

        self.assertEqual(payload["status"], "missing_destination")
        self.assertTrue(payload["attention_required"])
        self.assertFalse(payload["external_destination"])
        self.assertIn("external_alert_destination", payload["missing_conditions"])
        self.assertIn("alert_target_configured", payload["missing_conditions"])

    def test_alert_destination_payload_keeps_local_file_open(self) -> None:
        with patch.dict(os.environ, {"STOCKANALYSIS_ALERT_DESTINATION_MODE": "local_file"}, clear=True):
            payload = _build_alert_destination_payload(generated_at="2026-05-27T00:00:00Z")

        self.assertEqual(payload["status"], "local_only_not_external")
        self.assertTrue(payload["attention_required"])
        self.assertTrue(payload["local_only"])
        self.assertFalse(payload["external_destination"])

    def test_alert_destination_payload_closes_with_recent_external_test(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "alert-status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "mode": "webhook",
                        "destination_type": "discord",
                        "last_test_status": "passed",
                        "last_tested_at": "2026-05-26T23:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "STOCKANALYSIS_ALERT_DESTINATION_MODE": "webhook",
                    "STOCKANALYSIS_ALERT_DESTINATION_URL": "https://example.invalid/webhook",
                    "STOCKANALYSIS_ALERT_DESTINATION_STATUS_PATH": str(status_path),
                },
                clear=True,
            ):
                payload = _build_alert_destination_payload(generated_at="2026-05-27T00:00:00Z")

        self.assertEqual(payload["status"], "external_destination_verified")
        self.assertFalse(payload["attention_required"])
        self.assertTrue(payload["external_destination"])
        self.assertTrue(payload["target_configured"])
        self.assertTrue(payload["status_artifact_loaded"])
        self.assertEqual(payload["last_test_status"], "passed")
        self.assertTrue(payload["test_recent"])
        self.assertEqual(payload["missing_conditions"], [])

    def test_alert_destination_payload_accepts_ntfy_topic_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "alert-status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "mode": "ntfy",
                        "destination_type": "ntfy",
                        "last_test_status": "passed",
                        "last_tested_at": "2026-05-26T23:30:00Z",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "STOCKANALYSIS_ALERT_DESTINATION_MODE": "ntfy",
                    "STOCKANALYSIS_NTFY_TOPIC_URL": "https://ntfy.sh/private-topic-token",
                    "STOCKANALYSIS_ALERT_DESTINATION_STATUS_PATH": str(status_path),
                },
                clear=True,
            ):
                payload = _build_alert_destination_payload(generated_at="2026-05-27T00:00:00Z")

        self.assertEqual(payload["status"], "external_destination_verified")
        self.assertFalse(payload["attention_required"])
        self.assertEqual(payload["destination_type"], "ntfy")
        self.assertNotIn("private-topic-token", json.dumps(payload))

    def test_professional_source_gap_attention_policy_keeps_unguarded_gaps_open(self) -> None:
        self.assertTrue(
            _professional_source_gap_requires_attention(
                {
                    "status": "source_blockers_present",
                    "source_blocker_count": 1,
                    "guarded_source_blocked_recommendation_count": 0,
                    "coverage_gap_count": 0,
                    "fund_source_gap_count": 0,
                    "gaps": [
                        {
                            "product_type": "operating_company",
                            "blocker_type": "source_blocker",
                            "missing_layer_count": 3,
                            "professional_decision_use_allowed": True,
                            "paper_validation_input_allowed": True,
                            "active_recommendation_professional_use_blocked": False,
                        }
                    ],
                }
            )
        )
        self.assertFalse(
            _professional_source_gap_requires_attention(
                {
                    "status": "source_blockers_present",
                    "source_blocker_count": 1,
                    "guarded_source_blocked_recommendation_count": 1,
                    "coverage_gap_count": 0,
                    "fund_source_gap_count": 0,
                    "gaps": [
                        {
                            "product_type": "operating_company",
                            "blocker_type": "source_blocker",
                            "missing_layer_count": 6,
                            "professional_decision_use_allowed": False,
                            "paper_validation_input_allowed": False,
                            "active_recommendation_professional_use_blocked": True,
                        },
                        {
                            "product_type": "fund_or_etf",
                            "blocker_type": "fund_not_applicable",
                            "missing_layer_count": 0,
                            "professional_decision_use_allowed": True,
                            "paper_validation_input_allowed": True,
                            "active_recommendation_professional_use_blocked": False,
                        },
                    ],
                }
            )
        )

    def test_portfolio_review_managed_gate_policy_keeps_unmanaged_drift_open(self) -> None:
        safe_router = {
            "status": "loaded",
            "action_status": "no_op_wait_for_outcome_window",
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        }
        managed_history = {
            "status": "loaded",
            "decision_status": "review_required",
            "decision_count": 2,
            "review_required_count": 2,
            "guardrails": {
                "automatic_rebalance_allowed": False,
                "automatic_order_allowed": False,
                "broker_submit_allowed": False,
                "order_boundary": "read_only_no_order",
            },
        }
        history_policy = _portfolio_review_decision_history_attention_policy(
            managed_history,
            safe_router,
        )
        self.assertFalse(history_policy["attention_required"])
        self.assertEqual(history_policy["managed_review_status"], "waiting_for_outcome_window")
        unmanaged_router = {**safe_router, "status": "missing"}
        unmanaged_history_policy = _portfolio_review_decision_history_attention_policy(
            managed_history,
            unmanaged_router,
        )
        self.assertTrue(unmanaged_history_policy["attention_required"])

        managed_quality = {
            "status": "drift_outlier_review",
            "outlier_decisions": [{"symbol": "MSFT"}],
            "review_candidate_count": 1,
        }
        managed_drift_policy = _benchmark_drift_quality_attention_policy(
            managed_quality,
            {**managed_history, **history_policy},
            safe_router,
        )
        self.assertFalse(managed_drift_policy["attention_required"])
        self.assertEqual(
            managed_drift_policy["managed_review_status"],
            "review_recorded_waiting_for_outcome",
        )
        unmanaged_drift_policy = _benchmark_drift_quality_attention_policy(
            {**managed_quality, "outlier_decisions": []},
            {**managed_history, **history_policy},
            safe_router,
        )
        self.assertTrue(unmanaged_drift_policy["attention_required"])

    def test_recommendation_outcome_maturity_due_state_requests_calibration_now(self) -> None:
        payload = _build_recommendation_outcome_maturity_payload(
            {
                "status": "due_outcomes_ready",
                "as_of_date": "2026-06-20",
                "source_calibration_eval_run_id": 31,
                "horizon_days": [30, 90, 180, 365],
                "recommendation_horizon_count": 180,
                "recommendation_count": 45,
                "ready_for_backfill_count": 19,
                "due_today_count": 19,
                "overdue_count": 0,
                "price_gap_count": 0,
            }
        )

        action = payload["cadence_action"]
        self.assertEqual(action["status"], "run_outcome_calibration_now")
        self.assertTrue(action["should_run_now"])
        self.assertFalse(action["should_wait"])
        self.assertEqual(action["scheduler_job_id"], "recommendation-outcome-backfill-daily")
        self.assertIn("recommendation-outcome-calibration-sample-expansion-run", action["command"])
        self.assertIn("--as-of-date 2026-06-20", action["command"])
        self.assertTrue(action["blocks_weight_review"])
        self.assertFalse(action["automatic_weight_change_allowed"])

    def test_recommendation_outcome_maturity_overdue_state_requests_calibration_now(self) -> None:
        payload = _build_recommendation_outcome_maturity_payload(
            {
                "status": "overdue_outcomes_ready",
                "as_of_date": "2026-06-25",
                "source_calibration_eval_run_id": 31,
                "ready_for_backfill_count": 5,
                "overdue_count": 5,
            }
        )

        action = payload["cadence_action"]
        self.assertEqual(action["status"], "run_outcome_calibration_now")
        self.assertTrue(action["should_run_now"])
        self.assertIn("지연 5개", action["reason"])
        self.assertIn("--as-of-date 2026-06-25", action["command"])

    def test_recommendation_outcome_maturity_price_gap_state_requests_price_repair_first(self) -> None:
        payload = _build_recommendation_outcome_maturity_payload(
            {
                "status": "blocked_by_price_gaps",
                "as_of_date": "2026-06-20",
                "price_gap_count": 3,
                "missing_entry_price_count": 1,
                "missing_exit_price_count": 2,
            }
        )

        action = payload["cadence_action"]
        self.assertEqual(action["status"], "repair_price_history_then_calibrate")
        self.assertTrue(action["should_run_now"])
        self.assertTrue(action["requires_price_backfill"])
        self.assertIn("market-price-daily-run", action["command"])
        self.assertIn("recommendation-outcome-calibration-sample-expansion-run", action["follow_up_command"])
        self.assertTrue(action["blocks_weight_review"])

    def test_recommendation_outcome_due_action_router_payload_exposes_child_and_guardrails(self) -> None:
        payload = _build_recommendation_outcome_due_action_router_payload(
            {
                "status": "loaded",
                "eval_run_id": 71,
                "created_at": "2026-06-20T08:00:00+00:00",
                "as_of_date": "2026-06-20",
                "source_calibration_status": "loaded",
                "source_calibration_eval_run_id": 31,
                "source_calibration_summary": {
                    "status": "no_due_outcome_window",
                    "quality_status": "insufficient_sample",
                    "sample_status": "not_due",
                },
                "route_action": "execute_calibration",
                "action_status": "outcome_calibration_executed",
                "reason": "성과 산출 가능한 추천×기간 2개가 있어 outcome calibration을 실행할 수 있다.",
                "sample_audit_summary": {
                    "recommendation_horizon_count": 8,
                    "recommendation_count": 4,
                    "outcome_count": 2,
                    "ready_for_backfill_count": 0,
                    "not_due_count": 6,
                    "missing_entry_price_count": 0,
                    "missing_exit_price_count": 0,
                    "price_gap_count": 0,
                    "outcome_coverage_rate": 0.25,
                },
                "missing_reason_counts": {"not_due": 6},
                "missing_examples": [
                    {
                        "primary_symbol": "AAPL",
                        "recommendation_id": 147,
                        "as_of_date": "2026-05-21",
                        "horizon_day": 30,
                        "expected_measurement_end_date": "2026-06-20",
                        "sample_status": "not_due",
                    }
                ],
                "child_runner": {
                    "executed": True,
                    "report_name": "recommendation_outcome_calibration_sample_expansion",
                    "status": "completed",
                    "run_id": 9801,
                    "eval_run_id": 8801,
                    "calibration_status": "collect_more_outcomes_keep_weights",
                },
                "recommendation_scoring_mutated": False,
                "automatic_weight_change_allowed": False,
                "automatic_order_allowed": False,
                "broker_submit_allowed": False,
                "order_boundary": "read_only_no_order",
                "next_action": "calibration 결과를 확인한다.",
            }
        )

        self.assertEqual(payload["status"], "loaded")
        self.assertEqual(payload["eval_run_id"], "eval-run-71")
        self.assertEqual(payload["source_calibration_eval_run_id"], "eval-run-31")
        self.assertEqual(payload["sample_audit_summary"]["outcome_count"], 2)
        self.assertEqual(payload["missing_examples"][0]["recommendation_id"], "recommendation-147")
        self.assertTrue(payload["child_runner"]["executed"])
        self.assertEqual(payload["child_runner"]["run_id"], "pipeline-run-9801")
        self.assertFalse(payload["automatic_weight_change_allowed"])
        self.assertFalse(payload["broker_submit_allowed"])

    def test_live_data_health_response_opens_gate_for_failed_live_codex_invocations(self) -> None:
        class FailingAiExecutor(FakeLiveExecutor):
            def execute_scalar(self, sql: str) -> str:
                payload = json.loads(super().execute_scalar(sql))
                if sql.startswith("-- frontend data health state lookup"):
                    payload["live_ai_invocation_health"] = {
                        "status": "critical_ai_failed",
                        "window_hours": 48,
                        "recent_invocation_count": 30,
                        "recent_success_count": 0,
                        "recent_failed_count": 30,
                        "critical_failed_count": 30,
                        "critical_success_count": 0,
                        "latest_invocation_at": "2026-05-31T16:01:46+00:00",
                        "latest_failed_at": "2026-05-31T16:01:46+00:00",
                        "latest_failed_task_name": "news-rss-ai-extract",
                        "latest_error_summary": "token_invalidated 401 Unauthorized",
                        "latest_error_code": "codex_oauth_auth_invalid",
                        "task_health": [
                            {
                                "task_name": "news-rss-ai-extract",
                                "label": "뉴스 AI 구조화",
                                "critical": True,
                                "recent_invocation_count": 10,
                                "recent_success_count": 0,
                                "recent_failed_count": 10,
                                "latest_status": "failed",
                                "latest_created_at": "2026-05-31T16:01:46+00:00",
                                "latest_error_summary": "token_invalidated 401 Unauthorized",
                                "latest_error_code": "codex_oauth_auth_invalid",
                            }
                        ],
                        "next_action": "EC2 Codex OAuth 재로그인 후 뉴스 번역과 뉴스 AI 구조화 smoke를 즉시 다시 실행한다.",
                    }
                return json.dumps(payload)

        payload = resolve_live_frontend_response(
            "/api/data-health",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FailingAiExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        live_ai = payload["data"]["live_ai_invocation_health"]
        self.assertEqual(live_ai["status"], "critical_ai_failed")
        self.assertTrue(live_ai["attention_required"])
        self.assertEqual(live_ai["latest_failed_task_name"], "news-rss-ai-extract")
        self.assertIn("live_ai_invocation_health_attention", payload["data"]["open_gates"])
        gate_details = {item["gate_id"]: item for item in payload["data"]["open_gate_details"]}
        self.assertEqual(gate_details["live_ai_invocation_health_attention"]["label"], "실제 AI 호출")
        self.assertIn("Codex OAuth", gate_details["live_ai_invocation_health_attention"]["status_label"])

    def test_live_data_health_response_does_not_open_gate_for_recovered_live_codex_invocations(self) -> None:
        class RecoveredAiExecutor(FakeLiveExecutor):
            def execute_scalar(self, sql: str) -> str:
                payload = json.loads(super().execute_scalar(sql))
                if sql.startswith("-- frontend data health state lookup"):
                    payload["live_ai_invocation_health"] = {
                        "status": "recovered_with_recent_failures",
                        "window_hours": 48,
                        "recent_invocation_count": 40,
                        "recent_success_count": 10,
                        "recent_failed_count": 30,
                        "critical_failed_count": 30,
                        "critical_success_count": 10,
                        "latest_unhealthy_count": 0,
                        "critical_latest_unhealthy_count": 0,
                        "latest_invocation_at": "2026-05-31T16:20:46+00:00",
                        "latest_failed_at": "2026-05-31T16:01:46+00:00",
                        "latest_failed_task_name": "news-rss-ai-extract",
                        "latest_error_summary": "token_invalidated 401 Unauthorized",
                        "latest_error_code": "codex_oauth_auth_invalid",
                        "task_health": [
                            {
                                "task_name": "news-rss-ai-extract",
                                "label": "뉴스 AI 구조화",
                                "critical": True,
                                "recent_invocation_count": 20,
                                "recent_success_count": 10,
                                "recent_failed_count": 10,
                                "latest_status": "succeeded",
                                "latest_created_at": "2026-05-31T16:20:46+00:00",
                                "latest_error_summary": "",
                                "latest_error_code": "",
                            }
                        ],
                        "next_action": "과거 실패 이력은 남아 있지만 monitored AI 작업의 최신 실행은 성공했다.",
                    }
                return json.dumps(payload)

        payload = resolve_live_frontend_response(
            "/api/data-health",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=RecoveredAiExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        live_ai = payload["data"]["live_ai_invocation_health"]
        self.assertEqual(live_ai["status"], "recovered_with_recent_failures")
        self.assertFalse(live_ai["attention_required"])
        self.assertEqual(live_ai["latest_unhealthy_count"], 0)
        self.assertNotIn("live_ai_invocation_health_attention", payload["data"]["open_gates"])

    def test_live_data_health_response_includes_sanitized_scheduler_activation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "pending-approval-gate.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "data_operations_scheduler_activation_approval_gate",
                        "approval_gate": "blocked_pending_manual_approval",
                        "activation_allowed": False,
                        "scheduler_activation": "not_installed",
                        "host_install_path_written": False,
                        "launchctl_executed": False,
                        "child_command_executed": False,
                        "job_id": "market-price-daily",
                        "pipeline_name": "market_price_upsert",
                        "domain": "market",
                        "cadence": "daily",
                        "manual_next_step": "data-operations-live-scheduler-activation-request",
                        "generated_at": "2026-05-18T08:00:00Z",
                        "operator_dry_run_report_path": "/private/tmp/secret/evidence/operator-dry-run.json",
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_DATA_OPERATIONS_SCHEDULER_APPROVAL_GATE_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        activation = payload["data"]["scheduler"]["activation"]
        self.assertEqual(activation["status"], "pending_manual_approval")
        self.assertEqual(activation["job_id"], "market-price-daily")
        self.assertEqual(activation["pipeline_name"], "market_price_upsert")
        self.assertFalse(activation["activation_allowed"])
        self.assertEqual(activation["approval_gate"], "blocked_pending_manual_approval")
        self.assertEqual(activation["source"], "scheduler_activation_approval_gate_report")
        self.assertIn("scheduler_activation_manual_approval", payload["data"]["open_gates"])
        self.assertNotIn(str(report), json.dumps(activation))
        self.assertNotIn("operator-dry-run.json", json.dumps(activation))

    def test_live_data_health_response_uses_profile_scheduler_status_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "profile-scheduler-status.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "operating_data_profile_scheduler_status",
                        "status": "installed",
                        "install_status": "installed",
                        "scheduler_type": "systemd",
                        "timer_count": 5,
                        "active_timer_count": 5,
                        "generated_at": "2026-05-21T00:40:00Z",
                        "timers": [
                            {
                                "profile_id": "news-intraday",
                                "service_name": "stockanalysis-operating-data-news-intraday.service",
                                "timer_name": "stockanalysis-operating-data-news-intraday.timer",
                                "schedule": "Mon..Fri *-*-* 09..18:00/30 America/New_York",
                                "active_state": "active",
                                "next_elapse": "2026-05-21T13:00:00Z",
                                "last_result": "success",
                                "unit_path": "/etc/systemd/system/stockanalysis-operating-data-news-intraday.timer",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        scheduler = payload["data"]["scheduler"]
        self.assertEqual(scheduler["install_status"], "installed")
        self.assertEqual(scheduler["activation"]["status"], "installed")
        self.assertEqual(scheduler["profile_scheduler"]["scheduler_type"], "systemd")
        self.assertEqual(scheduler["profile_scheduler"]["active_timer_count"], 5)
        self.assertEqual(scheduler["profile_scheduler"]["timers"][0]["profile_id"], "news-intraday")
        self.assertNotIn(str(report), json.dumps(scheduler))
        self.assertNotIn("/etc/systemd/system", json.dumps(scheduler))
        self.assertNotIn("scheduler_activation_manual_approval", payload["data"]["open_gates"])

    def test_live_data_health_response_closes_production_api_gate_with_production_pool_evidence(self) -> None:
        pool_executor_type = type("PsycopgPoolExecutor", (FakeLiveExecutor,), {})
        with patch.dict(
            os.environ,
            {
                "STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE": "production",
                "STOCKANALYSIS_FRONTEND_API_SOURCE": "live",
                "STOCKANALYSIS_FRONTEND_API_AUTH_MODE": "read-token",
                "STOCKANALYSIS_FRONTEND_API_READ_TOKEN": "secret",
                "STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN": "https://stockanalysis.local",
            },
            clear=True,
        ):
            payload = resolve_live_frontend_response(
                "/api/data-health",
                config=RuntimeConfig(database_url="postgresql://example.invalid/db"),
                executor=pool_executor_type(),
                generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
            )

        production_api = payload["data"]["production_api_server"]
        self.assertEqual(production_api["status"], "production_ready")
        self.assertFalse(production_api["attention_required"])
        self.assertEqual(production_api["connection_boundary"], "psycopg_pool")
        self.assertNotIn("production_api_server", payload["data"]["open_gates"])
        auth_rbac = payload["data"]["auth_rbac"]
        self.assertEqual(auth_rbac["status"], "read_only_rbac_ready")
        self.assertFalse(auth_rbac["attention_required"])
        self.assertEqual(auth_rbac["read_role"], "viewer")
        self.assertNotIn("auth_rbac", payload["data"]["open_gates"])

    def test_live_data_health_response_closes_alert_gate_with_external_test_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "alert-status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "mode": "webhook",
                        "destination_type": "discord",
                        "last_test_status": "passed",
                        "last_tested_at": "2026-05-01T00:00:00Z",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {
                    "STOCKANALYSIS_ALERT_DESTINATION_MODE": "webhook",
                    "STOCKANALYSIS_ALERT_DESTINATION_URL": "https://example.invalid/webhook",
                    "STOCKANALYSIS_ALERT_DESTINATION_STATUS_PATH": str(status_path),
                },
                clear=True,
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        alert_destination = payload["data"]["alert_destination"]
        self.assertEqual(alert_destination["status"], "external_destination_verified")
        self.assertFalse(alert_destination["attention_required"])
        self.assertEqual(alert_destination["destination_type"], "discord")
        self.assertNotIn("alert_destination", payload["data"]["open_gates"])
        self.assertNotIn("https://example.invalid", json.dumps(alert_destination))

    def test_live_data_health_response_includes_sanitized_manual_ingest_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "manual-smoke.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "manual_local_ingest_smoke",
                        "generated_at": "2026-05-20T08:00:00Z",
                        "runtime_mode": "local_first",
                        "execute": False,
                        "smoke_status": "preview_not_executed",
                        "runtime_status": "ready",
                        "data_operations_env_file": "/private/tmp/hidden/data-operations.env",
                        "artifact_root": "/private/tmp/stockanalysis-runtime/artifacts",
                        "python_executable": "/private/tmp/stockanalysis-runtime/venv/bin/python",
                        "job_count": 2,
                        "planned_jobs": [
                            {"job_id": "market-price-daily", "command_argv": ["python", "ignored"]},
                            {"job_id": "news-rss-daily", "command_argv": ["python", "ignored"]},
                        ],
                        "artifact_runs": [],
                        "next_actions": ["review planned jobs"],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        smoke = payload["data"]["manual_local_ingest_smoke"]
        self.assertEqual(smoke["status"], "preview_not_executed")
        self.assertEqual(smoke["runtime_status"], "ready")
        self.assertEqual(smoke["planned_job_ids"], ["market-price-daily", "news-rss-daily"])
        self.assertEqual(smoke["source"], "manual_local_ingest_smoke_report")
        smoke_text = json.dumps(smoke)
        self.assertNotIn(str(report), smoke_text)
        self.assertNotIn("data-operations.env", smoke_text)
        self.assertNotIn("python_executable", smoke_text)

    def test_live_data_health_response_includes_sanitized_local_ingest_worker(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "local-worker.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "local_ingest_worker",
                        "generated_at": "2026-05-20T09:00:00Z",
                        "runtime_mode": "local_first",
                        "worker_status": "completed",
                        "execute": True,
                        "job_ids": ["market-price-daily", "news-rss-daily"],
                        "max_cycles": 1,
                        "completed_cycle_count": 1,
                        "failed_cycle_count": 0,
                        "interval_seconds": 0,
                        "stop_on_failure": True,
                        "latest_smoke_output_path": "/private/tmp/stockanalysis-runtime/manual-local-ingest-smoke.json",
                        "cycles": [
                            {
                                "cycle_number": 1,
                                "started_at": "2026-05-20T09:00:00Z",
                                "smoke_status": "passed",
                                "runtime_status": "ready",
                                "execute": True,
                                "job_count": 2,
                                "failed_job_count": 0,
                                "artifact_run_count": 2,
                            }
                        ],
                        "next_actions": ["open /data-health and verify"],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        worker = payload["data"]["local_ingest_worker"]
        self.assertEqual(worker["status"], "completed")
        self.assertTrue(worker["execute"])
        self.assertEqual(worker["completed_cycle_count"], 1)
        self.assertEqual(worker["failed_cycle_count"], 0)
        self.assertEqual(worker["job_ids"], ["market-price-daily", "news-rss-daily"])
        self.assertEqual(worker["cycles"][0]["smoke_status"], "passed")
        self.assertEqual(worker["source"], "local_ingest_worker_report")
        worker_text = json.dumps(worker)
        self.assertNotIn(str(report), worker_text)
        self.assertNotIn("data-operations.env", worker_text)
        self.assertNotIn("python_executable", worker_text)

    def test_live_data_health_response_includes_sanitized_cycle_ai_quality_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "cycle-ai-quality-audit.json"
            report.write_text(
                json.dumps(
                    {
                        "report_name": "cycle_ai_quality_audit",
                        "generated_at": "2026-05-24T00:00:00Z",
                        "execute": True,
                        "status": "completed",
                        "as_of_date": "2026-05-24",
                        "lookback_days": 30,
                        "audit_status": "attention_required",
                        "audit_score": 70,
                        "issue_count": 2,
                        "readiness_gap_count": 1,
                        "readiness_gaps": [
                            {
                                "gap_key": "cycle_snapshot_missing",
                                "label": "사이클 스냅샷 결과 없음",
                                "metric_key": "cycle_snapshot_count",
                                "current_value": 0,
                                "next_action": "run decision-daily or cycle-hierarchy-snapshot-v2-run",
                            }
                        ],
                        "metrics": {
                            "rss_document_count": 10,
                            "translated_document_count": 8,
                            "paper_validation_passed_count": 1,
                        },
                        "checks": {
                            "duplicate_title_count": 1,
                            "ungrounded_direct_ticker_count": 1,
                            "quantum_energy_mislink_count": 0,
                        },
                        "samples": {
                            "ungrounded_direct_tickers": [
                                {"event_id": 1, "symbol": "SPY", "event_title": "Fed risk"}
                            ],
                            "macro_false_tickers": [
                                {
                                    "event_id": 2,
                                    "symbol": "QQQ",
                                    "event_title": "Fed rate risk",
                                    "node_codes": ["MACRO_RATES_FED"],
                                }
                            ],
                            "normal_macro_flows": [
                                {
                                    "event_id": 3,
                                    "event_title": "Inflation cools",
                                    "node_codes": ["MACRO_INFLATION"],
                                }
                            ],
                        },
                        "next_actions": ["review direct ticker impacts without source-text grounding"],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_CYCLE_AI_QUALITY_AUDIT_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        audit = payload["data"]["cycle_ai_quality_audit"]
        self.assertEqual(audit["status"], "attention_required")
        self.assertEqual(audit["audit_score"], 70)
        self.assertEqual(audit["issue_count"], 2)
        self.assertEqual(audit["readiness_gap_count"], 1)
        self.assertEqual(audit["readiness_gaps"][0]["gap_key"], "cycle_snapshot_missing")
        self.assertEqual(audit["metrics"]["rss_document_count"], 10)
        self.assertEqual(audit["checks"]["ungrounded_direct_ticker_count"], 1)
        self.assertEqual(audit["samples"]["macro_false_tickers"][0]["symbol"], "QQQ")
        self.assertEqual(audit["samples"]["normal_macro_flows"][0]["event_title"], "Inflation cools")
        self.assertEqual(audit["source"], "cycle_ai_quality_audit_report")
        self.assertIn("cycle_ai_quality_audit_attention", payload["data"]["open_gates"])
        self.assertNotIn(str(report), json.dumps(audit))

    def test_live_data_health_response_degrades_invalid_scheduler_activation_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "invalid.json"
            report.write_text("not-json", encoding="utf-8")

            with patch.dict(
                os.environ,
                {"STOCKANALYSIS_DATA_OPERATIONS_SCHEDULER_APPROVAL_GATE_REPORT": str(report)},
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        activation = payload["data"]["scheduler"]["activation"]
        self.assertEqual(activation["status"], "invalid_report")
        self.assertEqual(activation["source"], "invalid_report")
        self.assertFalse(activation["activation_allowed"])

    def test_live_data_health_response_includes_sanitized_provider_budget_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = Path(tmpdir) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "alpha_vantage",
                        "days": {
                            "2024-11-01": {
                                "daily_budget": 25,
                                "used_request_count": 4,
                                "runs": [
                                    {
                                        "started_at": "2024-11-01T23:30:00Z",
                                        "status": "completed",
                                        "requested_symbol_count": 6,
                                        "provider_request_count": 4,
                                        "budget_remaining_after": 21,
                                    }
                                ],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH": str(ledger)}):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        budget = payload["data"]["provider_budget"]
        self.assertEqual(budget["status"], "configured")
        self.assertEqual(budget["daily_budget"], 25)
        self.assertEqual(budget["used_request_count"], 4)
        self.assertEqual(budget["remaining_request_count"], 21)
        self.assertEqual(budget["latest_run"]["provider_request_count"], 4)
        self.assertNotIn(str(ledger), json.dumps(budget))

    def test_live_data_health_response_reads_configured_market_price_provider_budget(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = Path(tmpdir) / "twelve-ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "twelve_data",
                        "days": {
                            "2024-11-01": {
                                "daily_budget": 800,
                                "used_request_count": 12,
                                "runs": [],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH": str(ledger),
                    "STOCKANALYSIS_MARKET_PRICE_PROVIDER": "twelvedata",
                },
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        budget = payload["data"]["provider_budget"]
        self.assertEqual(budget["status"], "configured")
        self.assertEqual(budget["provider"], "twelve_data")
        self.assertEqual(budget["daily_budget"], 800)
        self.assertEqual(budget["remaining_request_count"], 788)

    def test_live_data_health_response_uses_latest_provider_budget_day_when_current_day_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = Path(tmpdir) / "twelve-ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "version": "market-price-provider-budget-v1",
                        "provider": "twelve_data",
                        "days": {
                            "2024-10-31": {
                                "daily_budget": 800,
                                "used_request_count": 12,
                                "runs": [],
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(
                os.environ,
                {
                    "STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH": str(ledger),
                    "STOCKANALYSIS_MARKET_PRICE_PROVIDER": "twelve_data",
                },
            ):
                payload = resolve_live_frontend_response(
                    "/api/data-health",
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=FakeLiveExecutor(),
                    generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
                )

        budget = payload["data"]["provider_budget"]
        self.assertEqual(budget["status"], "stale")
        self.assertEqual(budget["provider"], "twelve_data")
        self.assertEqual(budget["budget_date"], "2024-10-31")
        self.assertEqual(budget["daily_budget"], 800)
        self.assertEqual(budget["remaining_request_count"], 788)
        self.assertNotEqual(date.fromisoformat(budget["budget_date"]), date.fromisoformat(payload["data"]["as_of_date"]))

    def test_data_health_sql_uses_operations_cadence_registry(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/data-health",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        sql = executor.scalar_sql[0]
        self.assertIn("with expected_jobs(", sql)
        self.assertIn("'portfolio_remediation_daily_automation'", sql)
        self.assertIn("'performance_outcome_schedule_bootstrap'", sql)
        self.assertIn("when run.status = 'succeeded_with_fallback' then 'degraded'", sql)
        self.assertIn("health_status in ('missing', 'stale', 'failed', 'degraded')", sql)
        self.assertIn("expected.job_id = 'portfolio-attribution-monthly'", sql)
        self.assertIn("then 'not_due'", sql)
        self.assertIn("data_health_local_clock", sql)
        self.assertIn("expected_jobs_with_due", sql)
        self.assertIn("America/New_York", sql)
        self.assertIn("latest_due_date_local", sql)
        self.assertIn("clock.local_now::date - 3", sql)
        self.assertIn("(run.ended_at at time zone 'America/New_York')::date", sql)
        self.assertIn("'data_operations_artifact_runner'", sql)
        self.assertIn("selected_risk_budget_guardrail", sql)
        self.assertIn("portfolio_risk_budget_guardrail", sql)
        self.assertIn("benchmark_drift", sql)
        self.assertIn("selected_news_ai_eval_quality", sql)
        self.assertIn("news_ai_extraction_quality", sql)
        self.assertIn("news-ai-eval-v1", sql)
        self.assertIn("news_ai_eval_quality", sql)
        self.assertIn("live_ai_task_catalog", sql)
        self.assertIn("live_ai_invocation_health", sql)
        self.assertIn("news-rss-korean-translation", sql)
        self.assertIn("news-rss-ai-extract", sql)
        self.assertIn("provider = 'codex_oauth'", sql)
        self.assertIn("active_recommendation_price_symbols", sql)
        self.assertIn("active_recommendation_price_freshness", sql)
        self.assertIn("recovered_with_recent_failures", sql)
        self.assertIn("selected_portfolio_review_decision_history", sql)
        self.assertIn("portfolio_review_decision_history", sql)
        self.assertIn("portfolio-review-decision-history-v1", sql)
        self.assertIn("selected_portfolio_review_decision_feedback", sql)
        self.assertIn("portfolio_review_decision_outcome_feedback", sql)
        self.assertIn("portfolio-review-decision-outcome-feedback-v1", sql)
        self.assertIn("selected_portfolio_review_feedback_calibration", sql)
        self.assertIn("portfolio_review_feedback_calibration", sql)
        self.assertIn("portfolio-review-feedback-calibration-v1", sql)
        self.assertIn("selected_portfolio_review_feedback_cadence", sql)
        self.assertIn("portfolio_review_feedback_cadence", sql)
        self.assertIn("portfolio-review-feedback-cadence-v1", sql)
        self.assertIn("selected_portfolio_review_feedback_action_router", sql)
        self.assertIn("portfolio_review_feedback_action_router", sql)
        self.assertIn("portfolio-review-feedback-action-router-v1", sql)
        self.assertIn("selected_recommendation_outcome_calibration", sql)
        self.assertIn("recommendation_outcome_calibration", sql)
        self.assertIn("recommendation-outcome-calibration-sample-expansion-v1", sql)
        self.assertIn("selected_recommendation_outcome_due_action_router", sql)
        self.assertIn("recommendation_outcome_due_action_router", sql)
        self.assertIn("recommendation-outcome-due-action-router-v1", sql)
        self.assertIn("outcome_maturity_classified", sql)
        self.assertIn("outcome_maturity_summary", sql)
        self.assertIn("recommendation_outcome_maturity", sql)
        self.assertIn("selected_recommendation_weight_review_readiness", sql)
        self.assertIn("recommendation_weight_review_readiness_audit", sql)
        self.assertIn("recommendation-weight-review-readiness-v1", sql)
        self.assertIn("professional_gap_active_recommendations", sql)
        self.assertIn("professional_source_gap_prioritization", sql)
        self.assertIn("professional_analysis_depth", sql)
        self.assertIn("professional_analysis_depth_summary", sql)
        self.assertIn("professional_analysis_depth_ranked", sql)
        self.assertIn("professional_recommendation_coverage_audit", sql)
        self.assertIn("professional_recommendation_coverage_audit_rows", sql)
        self.assertIn("selected_professional_audit_paper_validation", sql)
        self.assertIn("professional_gap_raw_filing_decision", sql)
        self.assertIn("professional_source_blocker_raw_filing_remediation", sql)
        self.assertIn("professional-source-blocker-raw-filing-remediation-v1", sql)
        self.assertIn("fund_company_financial_model_not_applicable", sql)
        self.assertIn("sec_companyfacts_missing_us_gaap_facts", sql)
        self.assertIn("professional-coverage-expansion-run", sql)
        self.assertIn("coverage_ratio", sql)

    def test_portfolio_review_decision_history_sql_reads_eval_artifact_without_mutation(self) -> None:
        sql = render_frontend_portfolio_review_decision_history_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("from ai.eval_run", sql)
        self.assertIn("portfolio_review_decision_history", sql)
        self.assertIn("portfolio-review-decision-history-v1", sql)
        self.assertIn("'automatic_order_allowed', false", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_portfolio_review_decision_feedback_sql_reads_eval_artifact_without_mutation(self) -> None:
        sql = render_frontend_portfolio_review_decision_feedback_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("from ai.eval_run", sql)
        self.assertIn("portfolio_review_decision_outcome_feedback", sql)
        self.assertIn("portfolio-review-decision-outcome-feedback-v1", sql)
        self.assertIn("'automatic_order_allowed', false", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_portfolio_review_feedback_calibration_sql_reads_eval_artifact_without_mutation(self) -> None:
        sql = render_frontend_portfolio_review_feedback_calibration_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("from ai.eval_run", sql)
        self.assertIn("portfolio_review_feedback_calibration", sql)
        self.assertIn("portfolio-review-feedback-calibration-v1", sql)
        self.assertIn("'automatic_order_allowed', false", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_portfolio_review_feedback_cadence_sql_reads_eval_artifact_without_mutation(self) -> None:
        sql = render_frontend_portfolio_review_feedback_cadence_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("from ai.eval_run", sql)
        self.assertIn("portfolio_review_feedback_cadence", sql)
        self.assertIn("portfolio-review-feedback-cadence-v1", sql)
        self.assertIn("'automatic_order_allowed', coalesce", sql)
        self.assertIn("'broker_submit_allowed', coalesce", sql)
        self.assertIn("'order_boundary', coalesce", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_portfolio_review_feedback_action_router_sql_reads_eval_artifact_without_mutation(self) -> None:
        sql = render_frontend_portfolio_review_feedback_action_router_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("from ai.eval_run", sql)
        self.assertIn("portfolio_review_feedback_action_router", sql)
        self.assertIn("portfolio-review-feedback-action-router-v1", sql)
        self.assertIn("'automatic_order_allowed', coalesce", sql)
        self.assertIn("'broker_submit_allowed', coalesce", sql)
        self.assertIn("'order_boundary', coalesce", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("from broker", lowered)
        self.assertNotIn("join broker", lowered)

    def test_live_stock_list_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/stocks?limit=1",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2024-12-02")
        self.assertEqual(payload["data"]["stock_count"], 2)
        self.assertEqual(payload["data"]["summary"]["recommended_stock_count"], 1)
        self.assertEqual(payload["pagination"]["limit"], 1)
        self.assertTrue(payload["pagination"]["has_more"])
        stock = payload["data"]["stocks"][0]
        self.assertEqual(stock["symbol"], "AAPL")
        self.assertEqual(stock["instrument_id"], "instrument-501")
        self.assertEqual(stock["latest_price"]["close"], 240.0)
        self.assertEqual(stock["latest_price"]["change_pct"], 0.01)
        self.assertEqual(stock["data_coverage"]["bar_count"], 31)
        self.assertEqual(stock["recommendation"]["recommendation_id"], "recommendation-7101")
        self.assertEqual(stock["position"]["linked_thesis_id"], "thesis-7001")

    def test_live_stock_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/stocks/AAPL",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["latest_price"]["close"], 240.0)
        self.assertEqual(payload["data"]["summary"]["return_pct"], 0.0435)
        self.assertEqual(payload["data"]["price_bars"][-1]["trade_date"], "2024-12-02")
        self.assertEqual(payload["data"]["recommendation"]["linked_thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["position"]["weight"], 0.05)
        self.assertEqual(payload["data"]["equity_research"]["artifact_id"], "equity-research-artifact-1201")
        self.assertEqual(payload["data"]["equity_research"]["title"], "AAPL 기업 리서치 요약")
        self.assertEqual(payload["data"]["equity_research"]["provider"], "fixture")
        self.assertEqual(payload["data"]["equity_research"]["source_run_id"], "pipeline-run-7711")
        self.assertEqual(
            payload["data"]["equity_research"]["source_document_ids"],
            ["source-document-aapl-2024-10k-20240928"],
        )
        self.assertEqual(payload["data"]["equity_research"]["valuation_sensitivity"]["margin_of_safety"], "watch")
        competitive_position = payload["data"]["industry_competitive_position"]
        self.assertEqual(competitive_position["position_id"], "industry-competitive-position-4101")
        self.assertEqual(competitive_position["competitive_position"], "leader")
        self.assertEqual(competitive_position["peer_group_id"], "peer-group-3101")
        self.assertEqual(competitive_position["peer_group_name"], "Large Cap Technology")
        self.assertEqual(competitive_position["moat_score"], 0.82)
        self.assertEqual(competitive_position["rivalry_risk_score"], 0.42)
        self.assertEqual(competitive_position["key_strengths"][0], "High profitability percentile")
        self.assertEqual(competitive_position["source_run_id"], "pipeline-run-779")
        financial_model = payload["data"]["financial_statement_model"]
        self.assertEqual(financial_model["status"], "partial")
        self.assertEqual(financial_model["statement_scope"], "annual")
        self.assertEqual(financial_model["latest_period_end"], "2024-09-28")
        self.assertEqual(financial_model["computed_metric_count"], 5)
        self.assertEqual(financial_model["data_gap_count"], 1)
        self.assertEqual(financial_model["source_run_ids"], ["pipeline-run-778"])
        self.assertIsNone(financial_model["source_data_blocker"])
        self.assertEqual(financial_model["metrics"][0]["label"], "매출 성장률")
        self.assertEqual(financial_model["metrics"][0]["history"][1]["metric_value"], 0.028)
        self.assertEqual(financial_model["sections"][0]["section_key"], "growth")
        self.assertEqual(financial_model["sections"][0]["metrics"][0]["metric_code"], "revenue_growth_yoy")
        self.assertEqual(financial_model["share_count"]["share_count_change_pct"], -0.0316)
        self.assertFalse(financial_model["automatic_order_allowed"])
        self.assertEqual(financial_model["score_policy"], "recommendation_weights_unchanged")
        target_range = payload["data"]["valuation_target_range"]
        self.assertValuationTargetRangeQuality(target_range, expected_status="usable")
        self.assertEqual(target_range["method_count"], 4)
        self.assertEqual(target_range["base_price"], 240.0)
        self.assertEqual(target_range["target_low"], 198.0)
        self.assertAlmostEqual(target_range["target_base"], 262.5)
        self.assertEqual(target_range["target_high"], 340.0)
        self.assertAlmostEqual(target_range["upside_base"], 0.09375)
        self.assertEqual(target_range["methods"][0]["method"], "dcf_lite")
        self.assertEqual(target_range["methods"][0]["data_quality"]["status"], "strong")
        self.assertEqual(target_range["methods"][0]["data_quality"]["data_gap_count"], 0)
        self.assertEqual(target_range["methods"][0]["assumption_items"][0]["label"], "가격 기준일")
        self.assertEqual(target_range["methods"][0]["assumption_items"][2]["value"], "2.8%")
        self.assertEqual(target_range["methods"][0]["sensitivity_cases"][1]["label"], "기준")
        self.assertAlmostEqual(target_range["methods"][0]["sensitivity_cases"][1]["upside"], 0.125)
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["status"], "available")
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["forecast_row_count"], 6)
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["scenario_count"], 3)
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["scenarios"][1]["scenario_key"], "base")
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["scenarios"][1]["terminal_revenue"], 450000000000.0)
        self.assertEqual(target_range["methods"][0]["forecast_evidence"]["scenarios"][1]["terminal_free_cash_flow"], 117000000000.0)
        self.assertIn("상세 매출·마진·CAPEX forecast", target_range["methods"][0]["limitations"][0])
        self.assertEqual(target_range["methods"][0]["source_run_id"], "pipeline-run-7801")
        sotp_method = next(method for method in target_range["methods"] if method["method"] == "sum_of_parts")
        self.assertEqual(sotp_method["method_label"], "SOTP")
        self.assertEqual(sotp_method["sotp_evidence"]["status"], "available")
        self.assertEqual(sotp_method["sotp_evidence"]["component_count"], 3)
        self.assertEqual(sotp_method["sotp_evidence"]["components"][0]["component_key"], "operating_business_fcf")
        self.assertEqual(sotp_method["sotp_evidence"]["components"][0]["fair_value_base"], 285.0)
        self.assertEqual(len(sotp_method["sotp_evidence"]["reported_segment_inputs"]), 2)
        self.assertEqual(sotp_method["sotp_evidence"]["reported_segment_inputs"][0]["segment_label"], "Products")
        self.assertEqual(sotp_method["sotp_evidence"]["reported_segment_inputs"][0]["revenue"], 391035000000.0)
        self.assertEqual(sotp_method["sotp_evidence"]["reported_segment_inputs"][0]["operating_income"], 153000000000.0)
        self.assertAlmostEqual(sotp_method["sotp_evidence"]["reported_segment_inputs"][0]["operating_margin"], 0.3913)
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_inputs"][0]["metric_unit"],
            "USD_millions_as_reported",
        )
        self.assertEqual(len(sotp_method["sotp_evidence"]["reported_segment_allocations"]), 2)
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_allocations"][0]["allocation_basis"],
            "operating_income_share",
        )
        self.assertAlmostEqual(
            sotp_method["sotp_evidence"]["reported_segment_allocations"][0]["allocation_weight"],
            0.7866,
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_allocations"][0]["allocated_fair_value_base"],
            224.181,
        )
        self.assertEqual(len(sotp_method["sotp_evidence"]["reported_segment_assumptions"]), 2)
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["driver_label"],
            "고마진 현금창출 사업부",
        )
        self.assertAlmostEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["base_growth_rate"],
            0.06,
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["base_multiple"],
            20.0,
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["driver_template_label"],
            "제품 교체 사이클·ASP·공급망",
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["calibration_method"],
            "multi_period_segment_trend_template",
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["history_period_count"],
            3,
        )
        self.assertAlmostEqual(
            sotp_method["sotp_evidence"]["reported_segment_assumptions"][0]["observed_revenue_cagr"],
            0.043,
        )
        self.assertEqual(sotp_method["sotp_evidence"]["segment_footnote_evidence"]["status"], "available")
        self.assertEqual(sotp_method["sotp_evidence"]["segment_footnote_evidence"]["evidence_count"], 3)
        self.assertEqual(
            sotp_method["sotp_evidence"]["segment_footnote_evidence"]["evidence_rows"][1]["metric_value"],
            391035000000.0,
        )
        self.assertEqual(
            sotp_method["sotp_evidence"]["segment_footnote_evidence"]["evidence_rows"][2]["evidence_type"],
            "segment_data_gap",
        )
        self.assertIn("SOTP", sotp_method["evidence_summary"])
        self.assertFalse(target_range["automatic_order_allowed"])
        self.assertEqual(target_range["score_policy"], "recommendation_weights_unchanged")
        self.assertEqual(payload["data"]["macro_flow_impacts"][0]["theme_key"], "MACRO_RATES_FED")
        self.assertEqual(payload["data"]["macro_flow_impacts"][0]["source_run_id"], "pipeline-run-7701")
        self.assertEqual(payload["data"]["recent_events"][0]["event_id"], "event-9001")
        self.assertEqual(payload["links"]["recommendation"], "/api/recommendations/recommendation-7101")
        self.assertEqual(payload["links"]["events"], "/api/events?asOfDate=2024-12-02&symbol=AAPL")

    def test_live_ai_evidence_neighborhood_response_matches_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai/evidence-neighborhoods/AAPL?asOfDate=2024-12-02&maxItems=25",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        data = payload["data"]
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(data["symbol"], "AAPL")
        self.assertEqual(data["retrieval_boundary"]["retrieval_backend"], "postgres_sql")
        self.assertEqual(data["retrieval_boundary"]["live_llm_call_enabled"], False)
        self.assertEqual(data["retrieval_boundary"]["token_budget"], 0)
        self.assertEqual(data["summary"]["event_count"], 1)
        self.assertEqual(data["summary"]["story_group_count"], 1)
        self.assertEqual(data["summary"]["ai_artifact_count"], 1)
        self.assertEqual(data["summary"]["embedded_chunk_count"], 1)
        self.assertEqual(data["internal_rag_context"]["status"], "ready")
        self.assertEqual(
            data["internal_rag_context"]["retrieval_policy"]["retrieval_backend"],
            "postgres_sql_graph_context",
        )
        self.assertFalse(data["internal_rag_context"]["retrieval_policy"]["live_llm_call_enabled"])
        self.assertFalse(data["internal_rag_context"]["retrieval_policy"]["write_enabled"])
        self.assertEqual(data["internal_rag_context"]["context_inventory"]["translated_event_count"], 1)
        self.assertIn("애플 2024년 10-K", data["internal_rag_context"]["prompt_context"]["context_text"])
        self.assertEqual(data["instrument"]["instrument_id"], "instrument-501")
        self.assertEqual(data["themes"][0]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(data["theme_edges"][0]["relation_type"], "contains")
        self.assertEqual(data["events"][0]["event_id"], "event-9001")
        self.assertEqual(data["events"][0]["korean_title"], "애플 2024년 10-K 연차 보고 이벤트")
        self.assertEqual(data["events"][0]["korean_summary"], "애플 연차 보고서가 장기 투자 논리 점검 근거로 연결됐다.")
        self.assertEqual(data["events"][0]["translation_confidence"], 0.91)
        self.assertEqual(data["events"][0]["source_document_id"], "source-document-aapl-2024-10k-20240928")
        self.assertEqual(data["story_groups"][0]["korean_title"], "애플 2024년 10-K 연차 보고 이벤트")
        self.assertEqual(data["story_groups"][0]["events"][0]["korean_title"], "애플 2024년 10-K 연차 보고 이벤트")
        self.assertEqual(data["ai_artifacts"][0]["evidence_id"], "ai-evidence-8801")
        self.assertEqual(data["evidence_chunks"][0]["embedding_status"], "indexed")
        self.assertEqual(data["evidence_chunks"][0]["source_url_host"], "www.sec.gov")
        self.assertEqual(data["evidence_chunks"][0]["source_text_kind"], "raw_html_text")
        self.assertFalse(data["evidence_chunks"][0]["used_metadata_fallback"])
        story_group = data["story_groups"][0]
        self.assertEqual(story_group["story_id"], "story-1")
        self.assertEqual(story_group["event_count"], 1)
        self.assertEqual(story_group["source_document_count"], 1)
        self.assertEqual(story_group["linked_chunk_count"], 1)
        self.assertEqual(story_group["events"][0]["event_id"], "event-9001")
        self.assertIn("same_title_signature", story_group["basis"])
        self.assertIn("same_source_document", story_group["basis"])
        self.assertIn("source-document-aapl-2024-10k-20240928", story_group["source_document_ids"])
        self.assertIn("chunk-30001", story_group["linked_chunk_ids"])
        self.assertTrue(story_group["relation_reasons"])
        self.assertNotIn("vector_storage_uri", json.dumps(data))
        self.assertNotIn("secret://", json.dumps(data))
        self.assertEqual(payload["links"]["stock"], "/api/stocks/AAPL")

    def test_live_ai_evidence_neighborhood_sql_uses_read_only_foundation_renderer(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        )

        sql = executor.scalar_sql[0]
        self.assertTrue(is_live_supported_path("/api/ai/evidence-neighborhoods/NVDA"))
        self.assertIn("-- ai evidence neighborhood lookup", sql)
        self.assertIn("'NVDA'", sql)
        self.assertIn("'2026-05-19'::date", sql)
        self.assertIn("limit 12", sql.lower())
        self.assertIn("ingest.source_document", sql)
        self.assertIn("chunk.chunk_metadata ->> 'source_text_kind'", sql)
        self.assertIn("https://news.google.com/%", sql)
        self.assertIn("ai.embedding_index", sql)
        self.assertNotIn("insert into", sql.lower())
        self.assertNotIn("update ", sql.lower())
        self.assertNotIn("delete from", sql.lower())

    def test_live_ai_news_cluster_list_response_matches_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai/news-clusters?asOfDate=2026-05-19&limit=10",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        )

        data = payload["data"]
        cluster = data["clusters"][0]
        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(data["as_of_date"], "2026-05-19")
        self.assertEqual(data["summary"]["cluster_count"], 1)
        self.assertEqual(data["summary"]["clustered_event_count"], 10)
        self.assertEqual(data["summary"]["embedded_chunk_count"], 2)
        self.assertEqual(data["summary"]["local_rule_cluster_count"], 1)
        self.assertEqual(data["summary"]["llm_candidate_invocation_count"], 5)
        self.assertEqual(data["summary"]["llm_candidate_success_count"], 3)
        self.assertEqual(data["summary"]["llm_candidate_failed_count"], 2)
        self.assertEqual(data["summary"]["llm_candidate_artifact_count"], 3)
        self.assertEqual(data["summary"]["latest_llm_invocation_status"], "failed")
        self.assertEqual(data["summary"]["latest_llm_provider"], "codex_oauth")
        self.assertEqual(cluster["evidence_id"], "ai-evidence-2")
        self.assertEqual(cluster["theme_key"], "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(cluster["story_key"], "theme")
        self.assertEqual(cluster["story_label"], "AI Semiconductor Cycle")
        self.assertEqual(cluster["symbols"], ["NVDA"])
        self.assertEqual(cluster["event_count"], 10)
        self.assertEqual(cluster["extraction_run"]["provider"], "local_rules")
        self.assertEqual(cluster["extraction_run"]["estimated_cost_usd"], 0.0)
        self.assertEqual(cluster["chunk_count"], 2)
        self.assertEqual(cluster["embedded_chunk_count"], 2)
        self.assertIn("같은 상위 테마로 묶임: AI_SEMICONDUCTOR_CYCLE", cluster["relation_reasons"])
        self.assertIn("직접 연결 종목: NVDA", cluster["relation_reasons"])
        self.assertIn("원천 문서 2개로 확인 가능", cluster["relation_reasons"])
        self.assertEqual(cluster["events"][0]["event_id"], "event-20")
        self.assertEqual(
            cluster["source_documents"][0]["source_document_id"],
            "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
        )
        self.assertNotIn("vector_storage_uri", json.dumps(data))
        self.assertNotIn("secret://", json.dumps(data))
        self.assertTrue(is_live_supported_path("/api/ai/news-clusters?asOfDate=2026-05-19"))

    def test_live_ai_news_cluster_list_allows_default_as_of_date_with_limit(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai/news-clusters?limit=10",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["summary"]["cluster_count"], 1)
        self.assertEqual(payload["data"]["clusters"][0]["evidence_id"], "ai-evidence-2")
        self.assertEqual(payload["pagination"]["limit"], 10)
        self.assertTrue(is_live_supported_path("/api/ai/news-clusters?limit=10"))

    def test_live_ai_news_cluster_list_sql_is_read_only(self) -> None:
        sql = render_frontend_ai_news_cluster_list_state_sql(
            as_of_date=datetime(2026, 5, 19, tzinfo=timezone.utc).date(),
            theme_key="AI_SEMICONDUCTOR_CYCLE",
            symbol="NVDA",
            page_limit=11,
            page_offset=0,
        )

        self.assertIn("-- frontend ai news cluster list state lookup", sql)
        self.assertIn("artifact.artifact_type = 'news_cluster_summary'", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("ai.document_chunk", sql)
        self.assertIn("ai.embedding_index", sql)
        self.assertIn("row_number() over", sql)
        self.assertIn("coalesce(nullif(cluster_summary ->> 'theme_key', ''), artifact_id::text)", sql)
        self.assertIn("coalesce(nullif(cluster_summary ->> 'story_key', ''), 'theme')", sql)
        self.assertIn("cluster_summary ->> 'theme_key' in ('MARKET_NEWS_FLOW', 'US_MARKET_BREADTH', 'UNCLASSIFIED')", sql)
        self.assertIn("story_split_artifact.cluster_summary ->> 'theme_key'", sql)
        self.assertIn("theme_artifact_rank = 1", sql)
        self.assertIn("as cluster_event_count", sql)
        self.assertIn("news_ai_candidate_invocation_stats as", sql)
        self.assertIn("task_name = 'news-rss-ai-extract'", sql)
        self.assertIn("'llm_candidate_failed_count'", sql)
        self.assertIn("'latest_llm_invocation_status'", sql)
        self.assertIn("cluster_artifacts.cluster_event_count desc", sql)
        self.assertIn("cluster_summary ->> 'theme_key' = 'AI_SEMICONDUCTOR_CYCLE'", sql)
        self.assertIn("upper(coalesce(event_item ->> 'symbol', '')) = 'NVDA'", sql)
        self.assertIn("limit 11", sql.lower())
        self.assertNotIn("insert into", sql.lower())
        self.assertNotIn("update ", sql.lower())
        self.assertNotIn("delete from", sql.lower())
        self.assertNotIn("vector_storage_uri", sql)

    def test_live_stock_sql_uses_canonical_tables(self) -> None:
        list_sql = render_frontend_stock_list_state_sql(as_of_date=datetime(2024, 12, 2).date())
        detail_sql = render_frontend_stock_detail_state_sql(symbol="AAPL", as_of_date=None)

        self.assertIn("market.daily_price_bar", list_sql)
        self.assertIn("signal.recommendation", list_sql)
        self.assertIn("portfolio.position_snapshot", list_sql)
        self.assertIn("limit 51", list_sql)
        self.assertIn("event.event_instrument_impact", detail_sql)
        self.assertIn("signal.propagated_instrument_impact", detail_sql)
        self.assertIn("research.equity_research_artifact", detail_sql)
        self.assertIn("research.industry_competitive_position", detail_sql)
        self.assertIn("market.valuation_snapshot", detail_sql)
        self.assertIn("latest_valuation_methods as", detail_sql)
        self.assertIn("'valuation_methods'", detail_sql)
        self.assertIn("market.financial_metric_normalized", detail_sql)
        self.assertIn("latest_financial_source_linkage_run as", detail_sql)
        self.assertIn("'source_data_blocker'", detail_sql)
        self.assertIn("fund_benchmark_source as", detail_sql)
        self.assertIn("fund_liquidity_summary as", detail_sql)
        self.assertIn("latest_fund_expense_ratio as", detail_sql)
        self.assertIn("latest_fund_nav as", detail_sql)
        self.assertIn("latest_fund_premium_discount as", detail_sql)
        self.assertIn("latest_fund_tracking_difference as", detail_sql)
        self.assertIn("'fund_instrument_analysis'", detail_sql)
        self.assertIn("'liquidity'", detail_sql)
        self.assertIn("tracking_difference_nav_%", detail_sql)
        self.assertIn("'tracking_difference_value'", detail_sql)
        self.assertIn("'nav_premium_discount'", detail_sql)
        self.assertIn("premium_discount_to_nav", detail_sql)
        self.assertIn("market.fund_metric_snapshot", detail_sql)
        self.assertIn("ref.benchmark_composition", detail_sql)
        self.assertIn("financial_metric_universe(metric_code)", detail_sql)
        self.assertIn("latest_financial_metrics as", detail_sql)
        self.assertIn("raw_share_count_rows as", detail_sql)
        self.assertIn("'financial_statement_model'", detail_sql)
        self.assertIn("'share_count'", detail_sql)
        self.assertIn("valuation.fair_value_low", detail_sql)
        self.assertIn("valuation.assumptions_json", detail_sql)
        self.assertIn("'equity_research'", detail_sql)
        self.assertIn("'industry_competitive_position'", detail_sql)
        self.assertIn("macro_flow_impacts as", detail_sql)
        self.assertIn("raw_recent_events as", detail_sql)
        self.assertIn("source_document.korean_title", detail_sql)
        self.assertIn("distinct on (coalesce(nullif(lower(title), ''), source_checksum, 'event:' || event_id::text))", detail_sql)
        self.assertIn("https://news.google.com/%", detail_sql)
        self.assertIn("limit 120", detail_sql)

    def test_live_paper_trading_preview_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/paper-trading/preview?limit=1",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["strategy_name"], "long_term_core")
        self.assertEqual(payload["data"]["quality_summary"]["recommendation_count"], 2)
        self.assertEqual(payload["data"]["quality_summary"]["hit_rate"], 1.0)
        self.assertEqual(payload["data"]["quality_summary"]["average_alpha"], 0.06)
        self.assertEqual(payload["data"]["quality_summary"]["position_recommendation_conflict_count"], 1)
        self.assertEqual(payload["pagination"]["limit"], 1)
        self.assertTrue(payload["pagination"]["has_more"])
        action = payload["data"]["paper_actions"][0]
        self.assertEqual(action["symbol"], "AAPL")
        self.assertEqual(action["instrument_id"], "instrument-501")
        self.assertEqual(action["recommendation_id"], "recommendation-7101")
        self.assertEqual(action["linked_thesis_id"], "thesis-7001")
        self.assertEqual(action["recommendation_action"], "exclude")
        self.assertEqual(action["recommendation_score"], 0.2579)
        self.assertEqual(action["current_weight"], 0.05)
        self.assertEqual(action["target_weight"], 0.0)
        self.assertEqual(action["paper_action"], "paper_sell_to_zero")
        self.assertEqual(action["risk_level"], "high")
        self.assertTrue(action["requires_human_approval"])
        self.assertTrue(action["conflict"])
        self.assertEqual(payload["links"]["stocks"], "/api/stocks")

    def test_live_paper_trading_preview_sql_uses_read_only_canonical_tables(self) -> None:
        sql = render_frontend_paper_trading_preview_state_sql(
            as_of_date=datetime(2024, 12, 2).date(),
            page_limit=6,
            page_offset=10,
        )

        self.assertIn("signal.recommendation", sql)
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("coalesce(recommendation.thesis_id, position.linked_thesis_id) as thesis_id", sql)
        self.assertIn("recommendation_id is null and current_weight > 0 and thesis_id is null", sql)
        self.assertIn("recommendation_id is null and current_weight > 0 and thesis_id is not null", sql)
        self.assertIn("select distinct on (outcome.recommendation_id)", sql)
        self.assertIn("limit 6", sql)
        self.assertIn("offset 10", sql)
        self.assertNotIn("insert into", sql.lower())
        self.assertNotIn("update ", sql.lower())
        self.assertNotIn("delete from", sql.lower())
        self.assertNotIn("from broker", sql.lower())
        self.assertNotIn("join broker", sql.lower())
        self.assertNotIn("order placement", sql.lower())

    def test_live_trading_readiness_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/trading/readiness",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["execution_mode"], "paper")
        self.assertEqual(payload["data"]["readiness_status"], "blocked")
        self.assertEqual(payload["data"]["gate_summary"]["pass_count"], 4)
        self.assertEqual(payload["data"]["gate_summary"]["blocked_count"], 3)
        self.assertEqual(payload["data"]["broker_boundary"]["broker_code"], "simulated_paper")
        self.assertFalse(payload["data"]["broker_boundary"]["secret_configured"])
        self.assertEqual(payload["data"]["account_permission"]["permission_scope"], "paper_trade")
        self.assertEqual(payload["data"]["order_limit_policy"]["max_single_order_notional"], 50000.0)
        self.assertTrue(payload["data"]["kill_switches"][0]["is_engaged"])
        self.assertEqual(payload["data"]["paper_validation"]["conflict_count"], 1)
        self.assertEqual(payload["data"]["portfolio_risk_budget_guardrail"]["eval_run_id"], "eval-run-23")
        self.assertEqual(
            payload["data"]["portfolio_risk_budget_guardrail"]["risk_gate_decision"],
            "blocked_by_risk_budget_review",
        )
        self.assertFalse(payload["data"]["portfolio_risk_budget_guardrail"]["paper_validation_input_allowed"])
        self.assertIn(
            "over_single_position_limit",
            payload["data"]["portfolio_risk_budget_guardrail"]["blocking_reasons"],
        )
        self.assertEqual(
            payload["data"]["portfolio_risk_budget_guardrail"]["benchmark_drift"]["status"],
            "calculated",
        )
        review = payload["data"]["portfolio_risk_budget_guardrail"]["rebalance_candidate_review"]
        self.assertEqual(review["status"], "review_required")
        self.assertEqual(review["candidate_count"], 4)
        self.assertEqual(review["candidates"][0]["symbol"], "TSLA")
        self.assertEqual(review["candidates"][0]["direction"], "overweight")
        self.assertEqual(review["candidates"][0]["severity"], "high")
        self.assertEqual(review["candidates"][0]["suggested_review_action"], "trim_active_overweight_review")
        self.assertEqual(review["candidates"][0]["order_boundary"], "read_only_no_order")
        self.assertEqual(review["candidates"][-1]["symbol"], "AMZN")
        self.assertEqual(review["candidates"][-1]["direction"], "underweight")
        self.assertEqual(review["candidates"][-1]["suggested_review_action"], "review_active_underweight_gap")
        self.assertEqual(payload["data"]["audit_summary"]["submitted_to_broker_count"], 0)
        self.assertEqual(payload["links"]["paper_trading_preview"], "/api/paper-trading/preview")
        self.assertNotIn("secret_ref", json.dumps(payload))

    def test_live_trading_readiness_sql_reads_safety_tables_without_exposing_secrets(self) -> None:
        sql = render_frontend_trading_readiness_state_sql(portfolio_name="Long Term Paper")
        lowered = sql.lower()

        self.assertIn("trading.broker_boundary", sql)
        self.assertIn("trading.account_permission", sql)
        self.assertIn("trading.order_limit_policy", sql)
        self.assertIn("trading.kill_switch_state", sql)
        self.assertIn("trading.paper_validation_run", sql)
        self.assertIn("trading.order_intent_audit", sql)
        self.assertIn("ai.eval_run", sql)
        self.assertIn("portfolio_risk_budget_guardrail", sql)
        self.assertIn("portfolio-risk-budget-guardrail-v1", sql)
        self.assertIn("benchmark_drift", sql)
        self.assertIn("'secret_configured', secret_ref is not null", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)
        self.assertNotIn("'secret_ref'", lowered)
        self.assertNotIn("submitted_to_broker = true", lowered)

    def test_live_cycle_state_list_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/cycles?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["strategy_name"], "long_term_core")
        self.assertEqual(payload["data"]["horizon_type"], "long_term")
        self.assertEqual(payload["data"]["universe_version"], "bootstrap-v1")
        self.assertEqual(payload["pagination"]["limit"], 50)
        self.assertEqual(payload["pagination"]["item_count"], 2)
        first_cycle = payload["data"]["cycle_states"][0]
        self.assertEqual(first_cycle["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(first_cycle["state"], "constructive")
        self.assertEqual(first_cycle["previous_state"], "neutral")
        self.assertEqual(first_cycle["confidence"], 0.72)
        self.assertEqual(first_cycle["instrument_count"], 1)
        self.assertEqual(first_cycle["top_symbols"], ["AAPL"])
        self.assertEqual(first_cycle["features"]["event_intensity"], 0.8)
        self.assertEqual(
            payload["links"]["theme_detail"],
            "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01",
        )

    def test_live_cycle_state_list_applies_limit(self) -> None:
        executor = FakeLiveExecutor()
        payload = resolve_live_frontend_response(
            "/api/cycles?asOfDate=2024-11-01&limit=1",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(len(payload["data"]["cycle_states"]), 1)
        self.assertEqual(payload["data"]["cycle_states"][0]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(payload["pagination"]["limit"], 1)
        self.assertTrue(payload["pagination"]["has_more"])
        self.assertIsNotNone(payload["pagination"]["next_cursor"])
        self.assertIn("limit 2", executor.scalar_sql[-1])

    def test_live_cycle_state_cursor_pushes_sql_offset(self) -> None:
        executor = FakeLiveExecutor()
        cursor = encode_frontend_cursor(25)

        resolve_live_frontend_response(
            f"/api/cycles?asOfDate=2024-11-01&limit=10&cursor={cursor}",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertIn("limit 11", executor.scalar_sql[-1])
        self.assertIn("offset 25", executor.scalar_sql[-1])

    def test_live_cycle_map_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/cycle-map?asOfDate=2024-11-01&limit=12",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["summary"]["node_count"], 3)
        self.assertEqual(payload["data"]["summary"]["hot_node_code"], "MACRO_RATES_FED")
        first_node = payload["data"]["nodes"][0]
        self.assertEqual(first_node["node_id"], "classification-node-101")
        self.assertEqual(first_node["node_code"], "MACRO_RATES_FED")
        self.assertEqual(first_node["cycle_level"], "macro")
        self.assertEqual(first_node["cycle_score"], 0.62)
        self.assertEqual(first_node["event_heat_score"], 0.81)
        self.assertEqual(first_node["conflict_flags"], ["growth_vs_rates"])
        self.assertEqual(first_node["top_symbols"], ["SPY", "QQQ", "TLT"])
        self.assertEqual(first_node["counts"]["propagated_impact_count"], 3)
        self.assertEqual(first_node["source_run_id"], "pipeline-run-9201")
        self.assertEqual(payload["data"]["edges"][0]["parent_code"], "MACRO_RATES_FED")
        self.assertEqual(payload["data"]["edges"][0]["child_code"], "TECH_DOMAIN")
        self.assertEqual(payload["data"]["edges"][0]["weight"], 0.75)
        self.assertEqual(payload["links"]["cycles"], "/api/cycles?asOfDate=2024-11-01")
        self.assertTrue(is_live_supported_path("/api/cycle-map?asOfDate=2024-11-01"))

    def test_live_cycle_map_sql_reads_graph_context_without_writes(self) -> None:
        sql = render_frontend_cycle_map_state_sql(as_of_date=date(2024, 11, 1), node_limit=12)
        lowered = sql.lower()

        self.assertIn("-- frontend cycle map state lookup", sql)
        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("ai.cycle_community_summary", sql)
        self.assertIn("ref.classification_edge", sql)
        self.assertIn("ref.instrument_factor_exposure", sql)
        self.assertIn("signal.propagated_instrument_impact", sql)
        self.assertIn("'top_symbols', canonical_top_symbols", sql)
        self.assertIn("node.code <> 'MARKET_NEWS_FLOW'", sql)
        self.assertIn("'cycle_community_ai_v2'", sql)
        self.assertIn("'cycle_graph_context_v1'", sql)
        self.assertIn("summary_json ->> 'korean_summary'", sql)
        self.assertIn("limit 12", lowered)
        self.assertIn("'nodes'", sql)
        self.assertIn("'edges'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_live_market_map_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/market-map?asOfDate=2026-06-05&limit=80",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 6, 5, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2026-06-05")
        self.assertEqual(payload["data"]["summary"]["status"], "partial_or_stale")
        self.assertFalse(payload["data"]["summary"]["recommendation_scoring_mutated"])
        self.assertEqual(payload["data"]["summary"]["order_boundary"], "read_only_no_order")
        first_group = payload["data"]["groups"][0]
        self.assertEqual(first_group["group_code"], "dollar")
        first_indicator = first_group["indicators"][0]
        self.assertEqual(first_indicator["indicator_code"], "USD_BROAD_INDEX")
        self.assertEqual(first_indicator["freshness_status"], "stale")
        self.assertIn("추정값으로 채우지 않는다", first_indicator["quality_note_ko"])
        self.assertEqual(payload["data"]["quality_flags"][0]["flag_code"], "stale_fred_dollar_index")
        self.assertEqual(payload["data"]["regimes"][0]["regime_code"], "dollar_liquidity_tightening")
        self.assertEqual(payload["data"]["news_links"][0]["document_id"], "source-document-501")
        self.assertTrue(is_live_supported_path("/api/market-map?asOfDate=2026-06-05"))

    def test_live_market_map_sql_reads_cross_asset_tables_without_writes(self) -> None:
        sql = render_frontend_market_map_state_sql(as_of_date=date(2026, 6, 5), indicator_limit=80)
        lowered = sql.lower()

        self.assertIn("-- frontend market map state lookup", sql)
        self.assertIn("market.market_indicator", sql)
        self.assertIn("signal.market_indicator_snapshot", sql)
        self.assertIn("signal.cross_asset_regime_snapshot", sql)
        self.assertIn("event.news_indicator_link", sql)
        self.assertIn("stale_fred_dollar_index", sql)
        self.assertIn("추정값으로 채우지 않는다", sql)
        self.assertIn("'groups'", sql)
        self.assertIn("'regimes'", sql)
        self.assertIn("'quality_flags'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_live_event_list_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/events?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["filters"]["event_type"], "all")
        self.assertEqual(payload["data"]["filters"]["evidence_type"], "all")
        self.assertEqual(payload["data"]["summary"]["event_count"], 1)
        self.assertEqual(payload["data"]["summary"]["ai_extracted_count"], 1)
        self.assertEqual(payload["data"]["summary"]["news_event_candidate_count"], 1)
        self.assertEqual(payload["data"]["summary"]["news_cluster_summary_count"], 0)
        self.assertEqual(payload["data"]["summary"]["unreviewed_event_count"], 0)
        event = payload["data"]["events"][0]
        self.assertEqual(event["event_id"], "event-9001")
        self.assertEqual(event["symbol"], "AAPL")
        self.assertEqual(event["instrument_id"], "instrument-501")
        self.assertEqual(event["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(event["impact_score"], 0.82)
        self.assertEqual(event["source_document_id"], "source-document-aapl-2024-10k-20240928")
        self.assertEqual(event["ai_evidence_id"], "ai-evidence-8801")
        self.assertEqual(event["ai_evidence_type"], "source_document_event")
        self.assertEqual(event["ai_evidence_provider"], "openai")
        self.assertEqual(event["ai_evidence_confidence"], 0.86)
        self.assertEqual(event["related_events"][0]["event_id"], "event-9002")
        self.assertEqual(event["related_events"][0]["relation_type"], "same_source_document")
        self.assertEqual(event["related_events"][0]["relation_strength"], 0.95)
        self.assertEqual(payload["links"]["theme_detail"], "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01")

    def test_live_theme_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(payload["data"]["state"], "constructive")
        self.assertEqual(payload["data"]["previous_state"], "neutral")
        self.assertEqual(payload["data"]["confidence"], 0.72)
        self.assertEqual(payload["data"]["cycle_score"], 0.74)
        self.assertEqual(payload["data"]["features"]["event_intensity"], 0.8)
        self.assertEqual(payload["data"]["cycle_history"][0]["state"], "neutral")
        linked_instrument = payload["data"]["linked_instruments"][0]
        self.assertEqual(linked_instrument["instrument_id"], "instrument-501")
        self.assertEqual(linked_instrument["active_thesis_id"], "thesis-7001")
        self.assertEqual(linked_instrument["latest_recommendation_id"], "recommendation-7101")
        supporting_event = payload["data"]["supporting_events"][0]
        self.assertEqual(supporting_event["event_id"], "event-9001")
        self.assertEqual(supporting_event["ai_evidence_id"], "ai-evidence-8801")
        self.assertEqual(payload["links"]["recommendation"], "/api/recommendations/recommendation-7101")

    def test_live_performance_outcomes_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["measurement_end_date"], "2024-12-02")
        self.assertEqual(payload["data"]["summary"]["measured_recommendation_count"], 1)
        self.assertEqual(payload["data"]["summary"]["hit_rate"], 1.0)
        self.assertEqual(payload["data"]["summary"]["average_alpha"], 0.06)
        outcome = payload["data"]["outcomes"][0]
        self.assertEqual(outcome["outcome_id"], "outcome-8101")
        self.assertEqual(outcome["recommendation_id"], "recommendation-7101")
        self.assertEqual(outcome["thesis_id"], "thesis-7001")
        self.assertEqual(outcome["alpha"], 0.06)
        self.assertEqual(outcome["source_run_id"], "pipeline-run-9102")
        component = payload["data"]["attribution_components"][0]
        self.assertEqual(component["component_id"], "attribution-component-8201")
        self.assertEqual(component["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(payload["data"]["coverage_exclusions"][0]["symbol"], "BABA")
        self.assertEqual(payload["data"]["quality_gates"][0]["status"], "blocked")
        quality_evaluation = payload["data"]["quality_evaluation"]
        self.assertEqual(quality_evaluation["status"], "insufficient_sample")
        self.assertEqual(quality_evaluation["measured_recommendation_count"], 1)
        self.assertEqual(quality_evaluation["review_outcome_mismatch_count"], 0)
        self.assertEqual(quality_evaluation["checks"][0]["check_key"], "sample_size")
        self.assertEqual(quality_evaluation["checks"][0]["status"], "warning")
        self.assertEqual(
            payload["links"]["coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_recommendation_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/recommendations/AAPL-2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["recommendation_id"], "recommendation-7101")
        self.assertEqual(payload["data"]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["instrument_id"], "instrument-501")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["score"], 0.78)
        self.assertEqual(payload["data"]["score_components"][0]["component"], "cycle_score")
        self.assertEqual(payload["data"]["score_components"][0]["value"], 0.74)
        self.assertEqual(payload["data"]["score_components"][0]["evidence_id"], "event-9001")
        self.assertEqual(payload["data"]["score_components"][1]["component"], "momentum_score")
        self.assertEqual(payload["data"]["score_components"][1]["provenance"]["source_type"], "market_feature")
        self.assertEqual(payload["data"]["score_components"][1]["provenance"]["feature_code"], "return_since_first_observation")
        self.assertEqual(payload["data"]["score_components"][1]["provenance"]["source_run_id"], "pipeline-run-9201")
        self.assertEqual(
            payload["data"]["score_components"][1]["provenance"]["evidence"]["first_trade_date"],
            "2024-10-01",
        )
        self.assertEqual(payload["data"]["score_components"][2]["component"], "rank_score")
        self.assertEqual(payload["data"]["score_components"][2]["evidence_id"], "universe-rank-aapl-2024-11-01-6101")
        self.assertEqual(payload["data"]["score_components"][2]["provenance"]["source_type"], "strategy_universe_rank")
        self.assertEqual(payload["data"]["score_components"][2]["provenance"]["universe_batch_id"], "strategy-universe-batch-6101")
        self.assertEqual(payload["data"]["score_components"][2]["provenance"]["rank_position"], 2)
        self.assertEqual(payload["data"]["score_components"][4]["component"], "macro_regime_score")
        self.assertEqual(payload["data"]["score_components"][4]["provenance"]["source_type"], "cycle_stack_context")
        self.assertEqual(
            payload["data"]["score_components"][4]["provenance"]["evidence"]["cycle_stack_node_code"],
            "MACRO_RATES_FED",
        )
        self.assertEqual(
            payload["data"]["score_components"][4]["provenance"]["evidence"]["cycle_stack_level"],
            "macro_regime",
        )
        fundamental_component = payload["data"]["score_components"][9]
        self.assertEqual(fundamental_component["component"], "fundamental_quality_score")
        self.assertEqual(fundamental_component["evidence_id"], "fundamental-aapl-2024-11-01-fundamental_quality_score")
        self.assertEqual(fundamental_component["provenance"]["source_type"], "fundamental_context")
        self.assertEqual(fundamental_component["provenance"]["label"], "재무 품질 근거")
        self.assertEqual(
            fundamental_component["provenance"]["evidence"]["fundamental_component_name"],
            "fundamental_quality_score",
        )
        self.assertIn(
            "financial quality",
            fundamental_component["provenance"]["evidence"]["fundamental_explanation"],
        )
        self.assertEqual(fundamental_component["weight"], 0.0)
        self.assertEqual(payload["data"]["equity_research"]["artifact_id"], "equity-research-artifact-1201")
        self.assertEqual(payload["data"]["equity_research"]["title"], "AAPL 기업 리서치 요약")
        self.assertEqual(payload["data"]["equity_research"]["provider"], "fixture")
        self.assertEqual(payload["data"]["equity_research"]["source_run_id"], "pipeline-run-7711")
        self.assertEqual(
            payload["data"]["equity_research"]["source_document_ids"],
            ["source-document-aapl-2024-10k-20240928"],
        )
        self.assertEqual(payload["data"]["equity_research"]["valuation_sensitivity"]["margin_of_safety"], "watch")
        competitive_position = payload["data"]["industry_competitive_position"]
        self.assertEqual(competitive_position["position_id"], "industry-competitive-position-4101")
        self.assertEqual(competitive_position["competitive_position"], "leader")
        self.assertEqual(competitive_position["peer_group_id"], "peer-group-3101")
        self.assertEqual(competitive_position["peer_group_name"], "Large Cap Technology")
        self.assertEqual(competitive_position["moat_score"], 0.82)
        self.assertEqual(competitive_position["rivalry_risk_score"], 0.42)
        self.assertEqual(competitive_position["key_risks"][0], "Large-cap technology rivalry remains material")
        self.assertEqual(competitive_position["source_run_id"], "pipeline-run-779")
        financial_model = payload["data"]["financial_statement_model"]
        self.assertEqual(financial_model["status"], "partial")
        self.assertEqual(financial_model["latest_period_end"], "2024-09-28")
        self.assertEqual(financial_model["computed_metric_count"], 5)
        self.assertEqual(financial_model["data_gap_count"], 1)
        self.assertEqual(financial_model["source_run_ids"], ["pipeline-run-778"])
        self.assertIsNone(financial_model["source_data_blocker"])
        self.assertEqual(financial_model["sections"][0]["section_key"], "growth")
        self.assertEqual(financial_model["sections"][0]["metrics"][0]["metric_code"], "revenue_growth_yoy")
        self.assertEqual(financial_model["sections"][2]["section_key"], "cash_flow")
        self.assertEqual(financial_model["share_count"]["share_count_change_pct"], -0.0316)
        self.assertEqual(financial_model["score_policy"], "recommendation_weights_unchanged")
        self.assertFalse(financial_model["automatic_order_allowed"])
        self.assertFalse(financial_model["broker_submit_allowed"])
        self.assertEqual(financial_model["order_boundary"], "read_only_no_order")
        target_range = payload["data"]["valuation_target_range"]
        self.assertValuationTargetRangeQuality(
            target_range,
            expected_status="review_required",
            expected_method_count=3,
            expected_missing_methods=["sum_of_parts"],
        )
        self.assertEqual(target_range["method_count"], 3)
        self.assertEqual(target_range["target_low"], 200.0)
        self.assertAlmostEqual(target_range["target_base"], 261.6666666667)
        self.assertEqual(target_range["target_high"], 330.0)
        self.assertAlmostEqual(target_range["upside_base"], 0.0902777778)
        self.assertEqual(target_range["order_boundary"], "read_only_no_order")
        self.assertEqual(payload["data"]["linked_thesis_id"], "thesis-7001")
        trace = payload["data"]["evidence_trace"]
        self.assertEqual(trace["symbol"], "AAPL")
        self.assertEqual(trace["direct_news_or_ai"]["status"], "linked")
        self.assertEqual(trace["direct_news_or_ai"]["event_id"], "event-9001")
        self.assertEqual(trace["direct_news_or_ai"]["ai_evidence_id"], "ai-evidence-8801")
        self.assertEqual(trace["direct_news_or_ai"]["korean_title"], "AAPL 연례 보고서 이벤트")
        self.assertEqual(trace["direct_news_or_ai"]["translation_confidence"], 0.91)
        self.assertEqual(trace["direct_news_or_ai"]["impact_strength"], 0.7)
        self.assertEqual(trace["macro_flow"]["propagated_impact_count"], 2)
        self.assertEqual(trace["macro_flow"]["source_run_id"], "pipeline-run-9301")
        self.assertEqual(trace["macro_flow"]["recent_flows"][0]["event_id"], "event-9101")
        self.assertEqual(
            trace["macro_flow"]["recent_flows"][0]["korean_title"],
            "연준 금리 경로가 장기 성장 기술주를 지지한다",
        )
        self.assertEqual(trace["macro_flow"]["recent_flows"][0]["impact_strength"], 0.52)
        self.assertEqual(trace["holding_review"]["status"], "review_linked")
        self.assertEqual(trace["holding_review"]["portfolio_review_id"], "portfolio-review-6001")
        self.assertEqual(trace["holding_review"]["review_item_id"], "portfolio-review-item-6101")
        self.assertEqual(trace["holding_review"]["source_run_id"], "pipeline-run-9401")
        self.assertEqual(trace["holding_review"]["position_linked_thesis_id"], "thesis-7001")
        review = payload["data"]["evidence_review"]
        self.assertEqual(review["quality_status"], "ai_review_passed")
        self.assertEqual(review["summary"]["score_component_count"], 14)
        self.assertEqual(review["summary"]["ai_evidence_component_count"], 1)
        self.assertEqual(review["summary"]["market_or_rank_component_count"], 3)
        self.assertEqual(review["summary"]["market_or_rank_provenance_count"], 3)
        self.assertTrue(review["summary"]["linked_thesis_present"])
        self.assertTrue(review["summary"]["outcome_measured"])
        self.assertEqual(review["gates"][2]["gate_key"], "ai_or_event_evidence")
        self.assertEqual(review["gates"][2]["status"], "pass")
        self.assertEqual(review["gates"][3]["gate_key"], "market_feature_provenance")
        self.assertEqual(review["gates"][3]["status"], "pass")
        self.assertEqual(review["gates"][-1]["gate_key"], "order_boundary")
        self.assertEqual(review["gates"][-1]["status"], "pass")
        waterfall = payload["data"]["professional_decision_waterfall"]
        self.assertEqual(waterfall["status"], "decision_review_ready")
        self.assertEqual(waterfall["score_policy"], "recommendation_weights_unchanged")
        self.assertFalse(waterfall["automatic_order_allowed"])
        self.assertFalse(waterfall["broker_submit_allowed"])
        self.assertEqual(waterfall["order_boundary"], "read_only_no_order")
        self.assertEqual(
            [step["step_key"] for step in waterfall["steps"]],
            [
                "macro_cycle",
                "news_ai",
                "business_competition",
                "financial_quality",
                "valuation",
                "thesis",
                "position_sizing",
                "paper_validation",
            ],
        )
        self.assertEqual(waterfall["steps"][0]["title"], "거시·사이클 배경")
        self.assertIn("연준 금리 경로", waterfall["steps"][0]["facts"][2]["value"])
        self.assertEqual(waterfall["steps"][3]["title"], "재무 품질")
        self.assertEqual(waterfall["steps"][3]["status"], "재무 모델 연결")
        self.assertIn("최근 재무 기간 2024-09-28", waterfall["steps"][3]["detail"])
        self.assertEqual(waterfall["steps"][3]["facts"][0]["label"], "최근 재무 기간")
        self.assertEqual(waterfall["steps"][3]["facts"][0]["value"], "2024-09-28")
        self.assertEqual(waterfall["steps"][3]["facts"][1]["value"], "5개")
        self.assertEqual(waterfall["steps"][3]["facts"][2]["value"], "1개")
        self.assertEqual(waterfall["steps"][3]["source"], "financial_statement_model_and_fundamental_context")
        self.assertEqual(waterfall["steps"][4]["title"], "밸류에이션")
        self.assertEqual(waterfall["steps"][4]["status"], "목표가 범위 연결")
        self.assertIn("USD 261.67", waterfall["steps"][4]["facts"][1]["value"])
        self.assertEqual(waterfall["steps"][4]["facts"][4]["value"], "3개")
        self.assertEqual(waterfall["steps"][6]["title"], "포지션 크기")
        self.assertEqual(waterfall["steps"][6]["facts"][0]["value"], "5.0%")
        self.assertEqual(waterfall["steps"][6]["facts"][2]["value"], "+0.5%")
        self.assertEqual(waterfall["steps"][7]["facts"][2]["value"], "읽기 전용 차단")
        self.assertTrue(all(step["order_boundary"] == "read_only_no_order" for step in waterfall["steps"]))
        professional_audit = payload["data"]["professional_evidence_audit"]
        self.assertEqual(professional_audit["status"], "ready_for_review")
        self.assertEqual(professional_audit["recommendation_id"], "recommendation-7101")
        self.assertEqual(professional_audit["symbol"], "AAPL")
        self.assertEqual(professional_audit["product_type"], "operating_company")
        self.assertEqual(professional_audit["expected_layer_count"], 9)
        self.assertEqual(professional_audit["available_layer_count"], 8)
        self.assertEqual(professional_audit["partial_layer_count"], 1)
        self.assertEqual(professional_audit["missing_layer_count"], 0)
        self.assertAlmostEqual(professional_audit["coverage_ratio"], 8.5 / 9)
        layer_statuses = {layer["key"]: layer["status"] for layer in professional_audit["layer_checks"]}
        self.assertEqual(layer_statuses["macro_cycle"], "complete")
        self.assertEqual(layer_statuses["financial_metric_normalized"], "partial")
        self.assertEqual(layer_statuses["valuation_snapshot"], "complete")
        self.assertEqual(layer_statuses["paper_validation"], "complete")
        self.assertFalse(professional_audit["recommendation_scoring_mutated"])
        self.assertFalse(professional_audit["automatic_weight_change_allowed"])
        self.assertFalse(professional_audit["broker_submit_allowed"])
        self.assertEqual(professional_audit["order_boundary"], "read_only_no_order")
        self.assertEqual(payload["data"]["outcome"]["alpha"], 0.06)
        self.assertEqual(payload["links"]["thesis"], "/api/theses/thesis-7001")
        self.assertEqual(payload["links"]["source_events"], "/api/events?asOfDate=2024-11-01&symbol=AAPL")

    def test_live_recommendation_list_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/recommendations?asOfDate=2024-11-01&limit=1",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2024-11-01")
        self.assertEqual(payload["data"]["recommendation_count"], 2)
        self.assertEqual(payload["data"]["summary"]["reviewable_count"], 1)
        self.assertEqual(payload["data"]["summary"]["blocked_count"], 1)
        self.assertEqual(payload["data"]["summary"]["average_score"], 0.5189)
        self.assertEqual(payload["data"]["summary"]["macro_flow_evidence_recommendation_count"], 1)
        self.assertEqual(payload["data"]["summary"]["decision_review_ready_count"], 1)
        self.assertEqual(payload["data"]["summary"]["paper_validation_pending_count"], 0)
        self.assertEqual(payload["data"]["summary"]["decision_blocked_count"], 1)
        self.assertEqual(payload["data"]["summary"]["order_blocked_count"], 2)
        self.assertEqual(payload["data"]["summary"]["evidence_quality_ready_count"], 1)
        self.assertEqual(payload["data"]["summary"]["evidence_quality_source_blocked_count"], 1)
        self.assertEqual(payload["pagination"]["limit"], 1)
        self.assertTrue(payload["pagination"]["has_more"])
        row = payload["data"]["recommendations"][0]
        self.assertEqual(row["recommendation_id"], "recommendation-7101")
        self.assertEqual(row["symbol"], "AAPL")
        self.assertEqual(row["instrument_id"], "instrument-501")
        self.assertEqual(row["score"], 0.78)
        self.assertEqual(row["recommended_weight"], 0.05)
        self.assertEqual(row["linked_thesis_id"], "thesis-7001")
        self.assertEqual(row["evidence"]["quality_status"], "ai_review_passed")
        self.assertEqual(row["evidence"]["primary_evidence_id"], "ai-evidence-8801")
        self.assertEqual(row["evidence"]["macro_flow_component_count"], 1)
        self.assertEqual(row["evidence"]["macro_flow_evidence_count"], 8)
        self.assertEqual(row["evidence_quality"]["status"], "ready_for_review")
        self.assertEqual(row["evidence_quality"]["title"], "핵심 근거 연결")
        self.assertEqual(row["evidence_quality"]["coverage_ratio"], 1.0)
        self.assertEqual(row["evidence_quality"]["available_layer_count"], 9)
        self.assertEqual(row["evidence_quality"]["expected_layer_count"], 9)
        self.assertEqual(row["evidence_quality"]["missing_layer_labels"], [])
        self.assertFalse(row["evidence_quality"]["automatic_weight_change_allowed"])
        self.assertFalse(row["evidence_quality"]["broker_submit_allowed"])
        self.assertEqual(row["evidence_quality"]["order_boundary"], "read_only_no_order")
        self.assertEqual(row["outcome"]["alpha"], 0.06)
        self.assertEqual(row["decision_boundary"]["status"], "decision_review_ready")
        self.assertTrue(row["decision_boundary"]["paper_validation_input_allowed"])
        self.assertFalse(row["decision_boundary"]["automatic_order_allowed"])
        self.assertFalse(row["decision_boundary"]["broker_submit_allowed"])
        self.assertEqual(row["decision_boundary"]["order_boundary"], "read_only_no_order")
        self.assertEqual(payload["links"]["paper_trading"], "/api/paper-trading/preview")
        self.assertTrue(is_live_supported_path("/api/recommendations?asOfDate=2024-11-01"))

    def test_live_recommendation_list_sql_uses_read_only_canonical_tables(self) -> None:
        sql = render_frontend_recommendation_list_state_sql(
            as_of_date=datetime(2024, 11, 1).date(),
            page_limit=6,
            page_offset=10,
        )
        lowered = sql.lower()

        self.assertIn("-- frontend recommendation list state lookup", sql)
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("signal.recommendation recommendation", sql)
        self.assertIn("signal.recommendation_score_component", sql)
        self.assertIn("macro_flow_component_count", sql)
        self.assertIn("macro_flow_evidence_count", sql)
        self.assertIn("signal.propagated_instrument_impact", sql)
        self.assertIn("'macro_flow_evidence_recommendation_count'", sql)
        self.assertIn("'decision_review_ready_count'", sql)
        self.assertIn("'paper_validation_pending_count'", sql)
        self.assertIn("'decision_blocked_count'", sql)
        self.assertIn("'order_blocked_count'", sql)
        self.assertIn("'evidence_quality'", sql)
        self.assertIn("'evidence_quality_ready_count'", sql)
        self.assertIn("'evidence_quality_source_blocked_count'", sql)
        self.assertIn("professional_source_linkage", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("research.industry_competitive_position", sql)
        self.assertIn("research.equity_research_artifact", sql)
        self.assertIn("recommendation_weights_unchanged", sql)
        self.assertIn("'decision_boundary'", sql)
        self.assertIn("'read_only_no_order'", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("'ai_review_passed'", sql)
        self.assertIn("limit 6", sql)
        self.assertIn("offset 10", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_live_recommendation_detail_sql_links_score_components_to_event_or_ai_evidence(self) -> None:
        sql = render_frontend_recommendation_detail_state_sql(identifier="AAPL-2024-11-01")
        lowered = sql.lower()

        self.assertIn("recommendation_event_anchor as", sql)
        self.assertIn("recommendation_evidence_anchor as", sql)
        self.assertIn("market_feature_provenance as", sql)
        self.assertIn("strategy_universe_provenance as", sql)
        self.assertIn("macro_flow_provenance as", sql)
        self.assertIn("macro_flow_all_rows as", sql)
        self.assertIn("macro_flow_recent_rows as", sql)
        self.assertIn("latest_position_trace as", sql)
        self.assertIn("portfolio_review_trace as", sql)
        self.assertIn("latest_equity_research as", sql)
        self.assertIn("research.equity_research_artifact", sql)
        self.assertIn("latest_industry_competitive_position as", sql)
        self.assertIn("research.industry_competitive_position", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("latest_valuation_methods as", sql)
        self.assertIn("'valuation_methods'", sql)
        self.assertIn("valuation.fair_value_base", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("latest_financial_source_linkage_run as", sql)
        self.assertIn("'source_data_blocker'", sql)
        self.assertIn("fund_benchmark_source as", sql)
        self.assertIn("fund_liquidity_summary as", sql)
        self.assertIn("latest_fund_expense_ratio as", sql)
        self.assertIn("latest_fund_nav as", sql)
        self.assertIn("latest_fund_premium_discount as", sql)
        self.assertIn("latest_fund_tracking_difference as", sql)
        self.assertIn("'fund_instrument_analysis'", sql)
        self.assertIn("'liquidity'", sql)
        self.assertIn("tracking_difference_nav_%", sql)
        self.assertIn("'tracking_difference_value'", sql)
        self.assertIn("'nav_premium_discount'", sql)
        self.assertIn("premium_discount_to_nav", sql)
        self.assertIn("market.fund_metric_snapshot", sql)
        self.assertIn("ref.benchmark_composition", sql)
        self.assertIn("financial_metric_universe(metric_code)", sql)
        self.assertIn("latest_financial_metrics as", sql)
        self.assertIn("financial_metric_history as", sql)
        self.assertIn("raw_share_count_rows as", sql)
        self.assertIn("'financial_statement_model'", sql)
        self.assertIn("'share_count'", sql)
        self.assertIn("signal.propagated_instrument_impact", sql)
        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("portfolio.review_item", sql)
        self.assertIn("(select count(*)::integer from macro_flow_all_rows)", sql)
        self.assertIn("from macro_flow_recent_rows", sql)
        self.assertIn("'macro-flow-' || lower(recommendation.primary_symbol)", sql)
        self.assertIn("score_component_rows as", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("'ai-evidence-' || artifact_id::text", sql)
        self.assertIn("'event-' || event_id::text", sql)
        self.assertIn("'return_since_first_observation'", sql)
        self.assertIn("'return_1d'", sql)
        self.assertIn("'universe-rank-' || lower(recommendation.primary_symbol)", sql)
        self.assertIn("'cycle-stack-' || lower(recommendation.primary_symbol)", sql)
        self.assertIn("'cycle_stack_context'", sql)
        self.assertIn("'cycle_stack_node_code', substring(component.explanation from 'Selected recommendation node: ([A-Z0-9_]+)')", sql)
        self.assertIn("'cycle_stack_level'", sql)
        self.assertIn("'fundamental-' || lower(recommendation.primary_symbol)", sql)
        self.assertIn("'fundamental_quality_score'", sql)
        self.assertIn("'valuation_margin_score'", sql)
        self.assertIn("'peer_relative_score'", sql)
        self.assertIn("'balance_sheet_risk_penalty'", sql)
        self.assertIn("'thesis_consistency_score'", sql)
        self.assertIn("'fundamental_context'", sql)
        self.assertIn("'fundamental_component_name', component.component_name", sql)
        self.assertIn("'fundamental_explanation', component.explanation", sql)
        self.assertIn("'equity_research'", sql)
        self.assertIn("'industry_competitive_position'", sql)
        self.assertIn("'provenance', provenance", sql)
        self.assertIn("'evidence_trace'", sql)
        self.assertIn("'direct_news_or_ai'", sql)
        self.assertIn("'holding_review'", sql)
        self.assertIn("component.component_name in ('cycle_score', 'event_quality', 'event_intensity', 'theme_mapping')", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_live_thesis_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/theses/AAPL-bootstrap-v1",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["status"], "active")
        self.assertEqual(payload["data"]["created_from_recommendation_id"], "recommendation-7101")
        self.assertEqual(payload["data"]["core_claims"][0], "Annual reporting event quality remains supportive.")
        self.assertEqual(payload["data"]["invalidation_conditions"][0]["current_status"], "not_triggered")
        self.assertEqual(payload["data"]["latest_review"]["review_id"], "thesis-review-8001")
        self.assertEqual(payload["data"]["latest_review"]["reviewed_at"], "2024-11-01T23:00:00Z")
        self.assertIn("조치 watch", payload["data"]["latest_review"]["summary"])
        self.assertIn("아직 관찰 후보", payload["data"]["latest_review"]["change_notes"])
        self.assertIn("watchlist_recommendation", payload["data"]["latest_review"]["change_notes"])
        self.assertIn("주문이나 가상 거래도 만들지 않았다", payload["data"]["latest_review"]["change_notes"])
        self.assertEqual(payload["data"]["latest_review"]["next_review_date"], "2024-12-01")
        lifecycle = payload["data"]["lifecycle"]
        self.assertEqual(lifecycle["source"], "equity_research_artifact")
        self.assertEqual(lifecycle["equity_research_artifact_id"], "equity-research-artifact-1201")
        self.assertEqual(lifecycle["readiness"]["status"], "complete")
        self.assertEqual(lifecycle["readiness"]["missing_items"], [])
        self.assertEqual(lifecycle["buy_case"]["summary"], "서비스 매출과 현금흐름 품질이 장기 투자 논리를 보강한다.")
        self.assertIn("신제품 사이클", lifecycle["catalysts"])
        self.assertIn("Service revenue keeps compounding", lifecycle["catalysts"])
        self.assertIn("중국 수요 둔화", lifecycle["risks"])
        self.assertIn(
            "마진 훼손이 두 분기 지속",
            [condition["condition"] for condition in lifecycle["invalidation_conditions"]],
        )
        self.assertEqual(lifecycle["valuation"]["margin_of_safety_view"], "watch")
        self.assertEqual(lifecycle["valuation"]["upside_case"], "서비스 성장 유지")
        self.assertEqual(lifecycle["review_cadence"]["next_review_date"], "2024-12-01")
        target_range = payload["data"]["valuation_target_range"]
        self.assertValuationTargetRangeQuality(
            target_range,
            expected_status="review_required",
            expected_method_count=3,
            expected_missing_methods=["sum_of_parts"],
        )
        self.assertEqual(target_range["method_count"], 3)
        self.assertAlmostEqual(target_range["target_base"], 261.6666666667)
        self.assertAlmostEqual(target_range["margin_of_safety"], 0.0902666667)
        self.assertEqual(target_range["order_boundary"], "read_only_no_order")
        self.assertEqual(payload["data"]["evidence"][0]["evidence_id"], "event-9001")
        self.assertEqual(payload["data"]["evidence"][0]["observed_at"], "2024-10-31T14:00:00Z")
        self.assertEqual(payload["data"]["evidence"][1]["evidence_id"], "performance-outcome-8101")
        self.assertEqual(payload["data"]["evidence"][1]["observed_at"], "2024-12-02T00:00:00Z")
        professional_gates = payload["data"]["professional_lifecycle_gates"]
        self.assertEqual(professional_gates["status"], "review_required")
        self.assertEqual(professional_gates["gate_count"], 8)
        self.assertEqual(professional_gates["blocked_count"], 0)
        self.assertGreaterEqual(professional_gates["warning_count"], 1)
        self.assertEqual(professional_gates["latest_evidence_at"], "2024-12-02T00:00:00Z")
        self.assertEqual(professional_gates["latest_reviewed_at"], "2024-11-01T23:00:00Z")
        self.assertEqual(
            [gate["gate_key"] for gate in professional_gates["gates"]],
            [
                "buy_case",
                "catalysts",
                "risks",
                "invalidation",
                "valuation",
                "review_cadence",
                "evidence_freshness",
                "order_boundary",
            ],
        )
        self.assertEqual(professional_gates["gates"][5]["status"], "warning")
        self.assertIn("다음 재검토일이 지났다", professional_gates["gates"][5]["detail"])
        self.assertEqual(professional_gates["gates"][6]["status"], "warning")
        self.assertIn("최신 근거가 최근 thesis review 이후", professional_gates["gates"][6]["detail"])
        self.assertFalse(professional_gates["automatic_order_allowed"])
        self.assertFalse(professional_gates["broker_submit_allowed"])
        self.assertEqual(professional_gates["order_boundary"], "read_only_no_order")
        self.assertTrue(all(gate["order_boundary"] == "read_only_no_order" for gate in professional_gates["gates"]))
        review = payload["data"]["evidence_review"]
        self.assertEqual(review["quality_status"], "ai_review_passed")
        self.assertEqual(review["summary"]["source_event_count"], 1)
        self.assertEqual(review["summary"]["performance_evidence_count"], 1)
        self.assertEqual(review["summary"]["invalidation_condition_count"], 1)
        self.assertTrue(review["summary"]["latest_review_present"])
        self.assertEqual(review["summary"]["blocked_count"], 0)
        self.assertEqual(review["gates"][0]["gate_key"], "source_events")
        self.assertEqual(review["gates"][-1]["gate_key"], "order_boundary")
        self.assertEqual(payload["links"]["recommendation"], "/api/recommendations/recommendation-7101")
        self.assertEqual(
            payload["links"]["portfolio_coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_ai_evidence_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai-evidence/sec-event-aapl-10k-20240928",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["evidence_id"], "ai-evidence-8801")
        self.assertEqual(payload["data"]["instrument"]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["instrument"]["instrument_id"], "instrument-501")
        self.assertEqual(payload["data"]["source_document_id"], "aapl-2024-10k-20240928")
        self.assertEqual(payload["data"]["classification"]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(payload["data"]["classification"]["impact_score"], 0.82)
        self.assertEqual(payload["data"]["extraction_run"]["run_id"], "pipeline-run-9201")
        self.assertEqual(payload["data"]["extraction_run"]["estimated_cost_usd"], 0.0184)
        self.assertEqual(payload["data"]["extracted_fields"][0]["source_chunk_id"], "chunk-business-overview")
        self.assertEqual(payload["data"]["source_chunks"][0]["chunk_id"], "chunk-business-overview")
        self.assertIsNone(payload["data"]["cluster_summary"])
        self.assertEqual(payload["data"]["cluster_events"], [])
        self.assertEqual(
            payload["links"]["source_document"],
            "/api/source-documents/aapl-2024-10k-20240928",
        )

    def test_live_ai_evidence_detail_response_exposes_news_cluster_artifact(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai-evidence/ai-evidence-2",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["data"]["evidence_type"], "news_cluster_summary")
        self.assertEqual(payload["data"]["extraction_run"]["provider"], "local_rules")
        self.assertEqual(payload["data"]["extraction_run"]["input_tokens"], 0)
        self.assertEqual(payload["data"]["extraction_run"]["estimated_cost_usd"], 0.0)
        self.assertEqual(payload["data"]["cluster_summary"]["theme_key"], "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(payload["data"]["cluster_summary"]["story_key"], "theme")
        self.assertEqual(payload["data"]["cluster_summary"]["story_label"], "AI Semiconductor Cycle")
        self.assertEqual(payload["data"]["cluster_summary"]["event_count"], 10)
        self.assertEqual(payload["data"]["cluster_summary"]["symbols"], ["NVDA"])
        self.assertEqual(payload["data"]["cluster_summary"]["representative_event_id"], "event-20")
        self.assertEqual(payload["data"]["cluster_events"][0]["event_id"], "event-20")
        self.assertEqual(payload["data"]["cluster_events"][0]["source_document_id"], "rss:ai-semiconductor-cycle:65353569b9948d8593917bae")

    def test_live_ai_evidence_detail_response_exposes_news_event_candidate_artifact(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/ai-evidence/ai-evidence-3",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 19, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["data"]["evidence_type"], "news_event_candidate")
        self.assertEqual(payload["data"]["extraction_run"]["provider"], "codex_oauth")
        self.assertEqual(payload["data"]["news_candidate"]["analysis_method"], "fixture_structured_news")
        self.assertEqual(payload["data"]["news_candidate"]["theme_impacts"][0]["target"], "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(payload["data"]["news_candidate"]["theme_impacts"][0]["impact_strength"], 0.74)
        self.assertEqual(payload["data"]["news_candidate"]["instrument_impacts"][0]["target"], "NVDA")
        self.assertEqual(payload["data"]["news_candidate"]["recommendation_relevance"], "watchlist")
        self.assertEqual(payload["data"]["retrieval_context_summary"]["known_themes"][0]["code"], "AI_SEMICONDUCTOR_CYCLE")
        trace = payload["data"]["visibility_trace"]
        self.assertEqual(trace["source"]["status"], "available")
        self.assertEqual(trace["translation"]["status"], "missing")
        self.assertEqual(trace["ai_structure"]["theme_impact_count"], 1)
        self.assertEqual(trace["ai_structure"]["instrument_impact_count"], 1)
        self.assertEqual(trace["validator"]["status"], "passed")
        self.assertFalse(trace["validator"]["blocked"])
        self.assertEqual(trace["recommendation_linkage"]["target_symbol"], "NVDA")
        self.assertEqual(trace["read_only_boundary"]["order_boundary"], "read_only_no_order")
        self.assertEqual([step["step_key"] for step in trace["steps"]], [
            "source",
            "translation",
            "ai_structure",
            "validator",
            "recommendation_linkage",
        ])

    def test_live_source_document_detail_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/source-documents/aapl-2024-10k-20240928",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["document_id"], "aapl-2024-10k-20240928")
        self.assertEqual(payload["data"]["source_type"], "sec_filing")
        self.assertEqual(payload["data"]["symbol"], "AAPL")
        self.assertEqual(payload["data"]["retrieval"]["source_run_id"], "pipeline-run-9301")
        self.assertEqual(payload["data"]["retrieval"]["fetched_at"], "2024-11-01T01:10:00Z")
        self.assertEqual(payload["data"]["excerpts"][0]["chunk_id"], "chunk-business-overview")
        self.assertEqual(payload["data"]["linked_evidence"][0]["evidence_id"], "ai-evidence-8801")
        self.assertFalse(payload["data"]["access_policy"]["browser_download_enabled"])
        self.assertEqual(payload["links"]["ai_evidence"], "/api/ai-evidence/ai-evidence-8801")

    def test_detail_live_sql_uses_current_schema_columns(self) -> None:
        cycle_sql = render_frontend_cycle_state_list_sql(as_of_date=datetime(2024, 11, 1).date())
        thesis_sql = render_frontend_thesis_detail_state_sql(identifier="thesis-7001")
        ai_evidence_sql = render_frontend_ai_evidence_detail_state_sql(identifier="ai-evidence-8801")

        self.assertIn("signal.cycle_state_snapshot", cycle_sql)
        self.assertIn("ref.instrument_classification_membership", cycle_sql)
        self.assertIn("outcome.success_grade", thesis_sql)
        self.assertNotIn("outcome.outcome_label", thesis_sql)
        self.assertIn("thesis.exit_conditions", thesis_sql)
        self.assertIn("research.equity_research_artifact", thesis_sql)
        self.assertIn("market.valuation_snapshot", thesis_sql)
        self.assertIn("latest_valuation_methods as", thesis_sql)
        self.assertIn("'valuation_methods'", thesis_sql)
        self.assertIn("'equity_research'", thesis_sql)
        self.assertIn("artifact.catalysts_json", thesis_sql)
        self.assertIn("artifact.valuation_sensitivity_json", thesis_sql)
        self.assertIn("source_document.korean_title", thesis_sql)
        self.assertIn("투자 논리는 주문이 아니라 추천, 사이클, 가격 근거", thesis_sql)
        self.assertIn("event.event_document_link", ai_evidence_sql)
        self.assertIn("output_json #>> '{event,title}'", ai_evidence_sql)
        self.assertIn("then (select artifact_type from selected_artifact)", ai_evidence_sql)
        self.assertIn("'news_event_candidate_rejected'", ai_evidence_sql)
        self.assertIn("then 'validator_blocked'", ai_evidence_sql)
        self.assertIn("output_json -> 'candidate'", ai_evidence_sql)
        self.assertIn("output_json -> 'retrieval_context_summary'", ai_evidence_sql)
        self.assertIn("output_json -> 'cluster'", ai_evidence_sql)
        self.assertIn("output_json -> 'events'", ai_evidence_sql)

    def test_live_evidence_sql_links_document_scoped_artifacts(self) -> None:
        as_of_date = datetime(2024, 11, 1).date()
        event_sql = render_frontend_event_list_state_sql(
            as_of_date=as_of_date,
            theme_key=None,
            symbol=None,
            event_type="all",
        )
        theme_sql = render_frontend_theme_detail_state_sql(
            theme_key="ANNUAL_REPORTING",
            as_of_date=as_of_date,
        )
        ai_evidence_sql = render_frontend_ai_evidence_detail_state_sql(identifier="source-document-aapl-10k")
        source_document_sql = render_frontend_source_document_detail_state_sql(
            identifier="source-document-aapl-10k",
        )

        self.assertIn("artifact.event_id = event_row.event_id", event_sql)
        self.assertIn("artifact.document_id = source_document.document_id", event_sql)
        self.assertIn("artifact.artifact_type", event_sql)
        self.assertIn("invocation.provider", event_sql)
        self.assertIn("artifact.artifact_type <> 'news_event_candidate_rejected'", event_sql)
        self.assertIn("when 'news_event_candidate' then 0", event_sql)
        self.assertIn("when 'news_cluster_summary' then 2", event_sql)
        self.assertIn("'news_event_candidate_count'", event_sql)
        self.assertIn("'news_cluster_summary_count'", event_sql)
        self.assertIn("'suppressed_low_signal_candidate_count'", event_sql)
        self.assertIn("'unreviewed_event_count'", event_sql)
        self.assertIn("document_instrument", event_sql)
        self.assertIn("left join lateral", event_sql)
        self.assertIn("impact.confidence desc nulls last", event_sql)
        self.assertIn("coalesce(instrument.primary_symbol, document_instrument.primary_symbol)", event_sql)
        self.assertNotIn("left join event.event_instrument_impact instrument_impact on", event_sql)
        self.assertNotIn("left join event.event_classification_impact classification_impact on", event_sql)
        self.assertIn("artifact.event_id = event_row.event_id", theme_sql)
        self.assertIn("artifact.document_id = source_document.document_id", theme_sql)
        self.assertIn("('event-' || event_row.event_id::text) =", ai_evidence_sql)
        self.assertIn("document.external_document_id = regexp_replace", ai_evidence_sql)
        self.assertIn("from selected_event_candidates candidate", ai_evidence_sql)
        self.assertIn("where impact.event_id = candidate.event_id", ai_evidence_sql)
        self.assertIn("document.external_document_id = regexp_replace", source_document_sql)

    def test_live_event_list_sql_can_filter_by_evidence_type(self) -> None:
        sql = render_frontend_event_list_state_sql(
            as_of_date=datetime(2026, 5, 22).date(),
            theme_key=None,
            symbol=None,
            event_type="all",
            evidence_type="news_event_candidate",
        )

        self.assertIn("and evidence.artifact_type = 'news_event_candidate'", sql)
        self.assertIn("event_rows_before_quality_filter", sql)
        self.assertIn("filtered_event_rows", sql)
        self.assertIn("source_data_source.source_name", sql)
        self.assertIn("rss_news:marketwatch-topstories", sql)
        self.assertIn("rss_news:yahoo-finance-news", sql)
        self.assertIn("coalesce(evidence.confidence, 0) < 0.6500", sql)
        self.assertIn("coalesce(instrument.primary_symbol, document_instrument.primary_symbol) is null", sql)
        self.assertIn("as is_low_signal_candidate", sql)
        self.assertIn("and not is_low_signal_candidate", sql)
        self.assertIn("'suppressed_low_signal_candidate_count'", sql)
        self.assertIn("when 'news_event_candidate' then 0", sql)
        self.assertNotIn("insert into", sql.lower())

    def test_live_event_list_sql_can_show_validator_blocked_candidates(self) -> None:
        sql = render_frontend_event_list_state_sql(
            as_of_date=datetime(2026, 5, 22).date(),
            theme_key=None,
            symbol=None,
            event_type="all",
            evidence_type="news_event_candidate_rejected",
        )

        self.assertIn("or 'news_event_candidate_rejected' = 'news_event_candidate_rejected'", sql)
        self.assertIn("and evidence.artifact_type = 'news_event_candidate_rejected'", sql)
        self.assertIn("when evidence.artifact_type = 'news_event_candidate_rejected' then 'validator_blocked'", sql)
        self.assertNotIn("and not is_low_signal_candidate", sql)
        self.assertNotIn("insert into", sql.lower())

    def test_live_event_list_sql_can_show_suppressed_low_signal_candidates(self) -> None:
        sql = render_frontend_event_list_state_sql(
            as_of_date=datetime(2026, 5, 22).date(),
            theme_key=None,
            symbol=None,
            event_type="all",
            evidence_type="news_event_candidate_suppressed",
        )

        self.assertIn("and evidence.artifact_type = 'news_event_candidate'", sql)
        self.assertIn("and is_low_signal_candidate", sql)
        self.assertNotIn("and not is_low_signal_candidate", sql)
        self.assertNotIn("insert into", sql.lower())

    def test_live_event_list_sql_keeps_raw_ledger_visible_while_counting_no_suppression(self) -> None:
        sql = render_frontend_event_list_state_sql(
            as_of_date=datetime(2026, 5, 22).date(),
            theme_key=None,
            symbol=None,
            event_type="all",
            evidence_type="all",
        )

        self.assertIn("rss_news:marketwatch-topstories", sql)
        self.assertIn("as is_low_signal_candidate", sql)
        self.assertNotIn("and not is_low_signal_candidate", sql)
        self.assertIn("else 0", sql)

    def test_live_remediation_tickets_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/remediation-tickets?status=open",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["generated_at"], "2026-05-01T00:00:00Z")
        self.assertEqual(payload["data"]["portfolio_name"], "Long Term Paper")
        self.assertEqual(payload["data"]["ticket_count"], 1)
        self.assertEqual(
            payload["data"]["status_counts"],
            {"open": 1, "in_progress": 0, "resolved": 0, "ignored": 0},
        )
        self.assertEqual(payload["data"]["allocation_policy"]["policy_name"], "global_default_long_term_guardrail")
        self.assertEqual(payload["data"]["allocation_policy"]["policy_scope"], "global")
        self.assertEqual(payload["data"]["allocation_policy"]["max_single_position_weight"], 0.25)
        self.assertEqual(payload["data"]["allocation_policy"]["min_rebalance_target_weight"], 0.1)
        ticket = payload["data"]["tickets"][0]
        self.assertEqual(ticket["ticket_id"], "remediation-ticket-42")
        self.assertEqual(ticket["instrument_id"], "instrument-502")
        self.assertEqual(ticket["symbol"], "BABA")
        self.assertEqual(ticket["source_run_id"], "pipeline-run-9101")
        self.assertEqual(ticket["created_at"], "2024-11-01T23:30:00Z")
        self.assertEqual(
            payload["links"]["portfolio_coverage"],
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
        )

    def test_live_portfolio_coverage_response_matches_frontend_contract_shape(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=FakeLiveExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["coverage_measurement_end_date"], "2024-12-02")
        self.assertEqual(payload["data"]["summary"]["position_count"], 2)
        self.assertEqual(payload["data"]["summary"]["covered_position_count"], 1)
        self.assertEqual(payload["data"]["summary"]["missing_thesis_count"], 1)
        self.assertEqual(payload["data"]["summary"]["covered_weight"], 0.05)
        self.assertEqual(payload["data"]["summary"]["missing_thesis_weight"], 0.03)
        self.assertEqual(payload["data"]["summary"]["cash_weight"], 0.92)
        self.assertEqual(payload["data"]["summary"]["weight_coverage_ratio"], 0.625)
        self.assertEqual(payload["data"]["allocation_policy"]["policy_name"], "global_default_long_term_guardrail")
        self.assertEqual(payload["data"]["allocation_policy"]["max_single_position_weight"], 0.25)
        self.assertEqual(payload["data"]["allocation_policy"]["max_sector_weight"], 0.45)
        self.assertEqual(payload["data"]["allocation_policy"]["max_theme_weight"], 0.4)
        self.assertEqual(payload["data"]["risk_budget"]["status"], "within_budget")
        self.assertEqual(payload["data"]["risk_budget"]["largest_position_symbol"], "AAPL")
        self.assertEqual(payload["data"]["risk_budget"]["largest_position_weight"], 0.05)
        self.assertEqual(payload["data"]["risk_budget"]["over_single_position_limit_count"], 0)
        self.assertEqual(payload["data"]["risk_budget"]["below_rebalance_floor_count"], 2)
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["status"], "within_budget")
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["sector_exposures"][0]["exposure_key"], "TECHNOLOGY")
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["sector_exposures"][0]["exposure_weight"], 0.05)
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["theme_exposures"][0]["exposure_key"], "ANNUAL_REPORTING")
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["unclassified_weight"], 0.0)
        self.assertEqual(payload["data"]["risk_budget"]["rebalance_priorities"][0]["symbol"], "BABA")
        self.assertEqual(payload["data"]["risk_budget"]["rebalance_priorities"][0]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["risk_budget"]["rebalance_priorities"][0]["order_boundary"], "read_only_no_order")
        review = payload["data"]["risk_budget"]["rebalance_candidate_review"]
        self.assertEqual(review["status"], "review_required")
        self.assertEqual(review["candidate_count"], 2)
        self.assertEqual(review["decision_counts"]["reduce_watch"], 2)
        self.assertEqual(review["candidates"][0]["symbol"], "TSLA")
        self.assertEqual(review["candidates"][0]["review_decision"], "reduce_watch")
        self.assertEqual(review["candidates"][0]["decision_label"], "비중 축소 검토")
        self.assertTrue(review["candidates"][0]["professional_review_required"])
        self.assertEqual(review["candidates"][0]["source_evidence"]["benchmark_code"], "SPY")
        self.assertEqual(review["candidates"][0]["source_evidence"]["source_type"], "provider_file")
        self.assertEqual(review["candidates"][0]["links"]["stock"], "/stocks/TSLA")
        self.assertEqual(review["candidates"][0]["decision_path"][-1]["step"], "order_boundary")
        self.assertFalse(review["candidates"][0]["automatic_order_allowed"])
        self.assertFalse(review["candidates"][0]["broker_submit_allowed"])
        self.assertEqual(review["candidates"][0]["order_boundary"], "read_only_no_order")
        sizing = payload["data"]["risk_budget"]["position_sizing_review"]
        self.assertEqual(sizing["status"], "review_required")
        self.assertEqual(sizing["candidate_count"], 2)
        self.assertEqual(sizing["review_required_count"], 1)
        self.assertFalse(sizing["automatic_order_allowed"])
        self.assertFalse(sizing["broker_submit_allowed"])
        self.assertEqual(sizing["order_boundary"], "read_only_no_order")
        self.assertEqual(sizing["candidates"][0]["symbol"], "BABA")
        self.assertEqual(sizing["candidates"][0]["review_band"], "add_blocked_until_evidence")
        self.assertIn("thesis_missing", sizing["candidates"][0]["blocking_factors"])
        self.assertEqual(sizing["candidates"][1]["symbol"], "AAPL")
        self.assertEqual(sizing["candidates"][1]["review_band"], "watch_small_position")
        self.assertEqual(sizing["candidates"][1]["equity_research_artifact_id"], "equity-research-artifact-1201")
        self.assertIn("positive_margin_of_safety", sizing["candidates"][1]["supporting_factors"])
        history = payload["data"]["risk_budget"]["review_decision_history"]
        self.assertEqual(history["status"], "loaded")
        self.assertEqual(history["eval_run_id"], "eval-run-52")
        self.assertEqual(history["decision_count"], 2)
        self.assertEqual(history["top_decision"]["symbol"], "TSLA")
        self.assertFalse(history["guardrails"]["automatic_rebalance_allowed"])
        self.assertFalse(history["guardrails"]["broker_submit_allowed"])
        self.assertEqual(history["guardrails"]["order_boundary"], "read_only_no_order")
        feedback = payload["data"]["risk_budget"]["review_decision_feedback"]
        self.assertEqual(feedback["status"], "loaded")
        self.assertEqual(feedback["eval_run_id"], "eval-run-53")
        self.assertEqual(feedback["feedback_status"], "too_early")
        self.assertEqual(feedback["top_feedback"]["symbol"], "TSLA")
        self.assertFalse(feedback["guardrails"]["automatic_rebalance_allowed"])
        self.assertFalse(feedback["guardrails"]["broker_submit_allowed"])
        self.assertEqual(feedback["guardrails"]["order_boundary"], "read_only_no_order")
        calibration = payload["data"]["risk_budget"]["review_feedback_calibration"]
        self.assertEqual(calibration["status"], "loaded")
        self.assertEqual(calibration["eval_run_id"], "eval-run-54")
        self.assertEqual(calibration["calibration_status"], "insufficient_history")
        self.assertFalse(calibration["attention_required"])
        self.assertTrue(calibration["managed_wait"])
        self.assertEqual(calibration["feedback_run_count"], 1)
        self.assertEqual(calibration["family_summaries"][0]["decision_family"], "benchmark_drift")
        self.assertEqual(calibration["symbol_summaries"][0]["symbol"], "TSLA")
        self.assertFalse(calibration["guardrails"]["automatic_rebalance_allowed"])
        self.assertFalse(calibration["guardrails"]["broker_submit_allowed"])
        self.assertEqual(calibration["guardrails"]["order_boundary"], "read_only_no_order")
        cadence = payload["data"]["risk_budget"]["review_feedback_cadence"]
        self.assertEqual(cadence["status"], "loaded")
        self.assertEqual(cadence["eval_run_id"], "eval-run-55")
        self.assertEqual(cadence["cadence_status"], "wait_for_outcome_window")
        self.assertEqual(cadence["action_type"], "wait")
        self.assertFalse(cadence["should_run_now"])
        self.assertTrue(cadence["should_wait"])
        self.assertEqual(cadence["history"]["eval_run_id"], "eval-run-52")
        self.assertEqual(cadence["feedback"]["eval_run_id"], "eval-run-53")
        self.assertEqual(cadence["calibration"]["eval_run_id"], "eval-run-54")
        self.assertEqual(cadence["evidence"]["paper_validation"]["paper_validation_run_id"], "paper-validation-12")
        self.assertFalse(cadence["automatic_order_allowed"])
        self.assertFalse(cadence["broker_submit_allowed"])
        self.assertEqual(cadence["order_boundary"], "read_only_no_order")
        action_router = payload["data"]["risk_budget"]["review_feedback_action_router"]
        self.assertEqual(action_router["status"], "loaded")
        self.assertEqual(action_router["eval_run_id"], "eval-run-56")
        self.assertEqual(action_router["source_cadence_eval_run_id"], "eval-run-55")
        self.assertEqual(action_router["route_action"], "no_op")
        self.assertEqual(action_router["action_status"], "no_op_wait_for_outcome_window")
        self.assertFalse(action_router["child_runner"]["executed"])
        self.assertEqual(action_router["child_runner"]["status"], "not_run")
        self.assertFalse(action_router["automatic_order_allowed"])
        self.assertFalse(action_router["broker_submit_allowed"])
        self.assertEqual(action_router["order_boundary"], "read_only_no_order")
        self.assertEqual(payload["data"]["positions"][0]["active_thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["positions"][0]["outcome_status"], "measured")
        self.assertEqual(payload["data"]["positions"][0]["position_size_status"], "below_rebalance_floor")
        self.assertEqual(payload["data"]["positions"][0]["weight_to_single_position_limit"], 0.2)
        self.assertEqual(payload["data"]["positions"][1]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["attribution_readiness"]["blocking_reasons"], ["missing_thesis:BABA"])

    def test_benchmark_rebalance_candidate_review_keeps_related_context_read_only(self) -> None:
        review = _build_benchmark_rebalance_candidate_review_payload(
            {
                "status": "loaded",
                "benchmark_drift": {
                    "status": "calculated",
                    "benchmark_code": "SPY",
                    "benchmark_source": "ssga_spdr_spy_daily_holdings",
                    "source_type": "provider_file",
                    "source_as_of_date": "2026-05-21",
                    "drift_calculated": True,
                    "component_count": 503,
                    "composition_coverage_weight": "0.99837820",
                    "active_share": "0.21000000",
                    "top_active_positions": [
                        {
                            "symbol": "AAPL",
                            "portfolio_weight": "0.22710000",
                            "benchmark_weight": "0.07007801",
                            "active_weight": "0.15702199",
                        }
                    ],
                },
            },
            position_context_by_symbol={
                "AAPL": {
                    "active_thesis_id": "thesis-7001",
                    "recommendation_id": 7101,
                    "recommendation_action": "monitor_or_accumulate",
                    "recommended_weight": "0.0500",
                }
            },
        )

        candidate = review["candidates"][0]
        self.assertEqual(candidate["review_decision"], "reduce_watch")
        self.assertEqual(candidate["related_thesis_id"], "thesis-7001")
        self.assertEqual(candidate["related_recommendation_id"], "recommendation-7101")
        self.assertEqual(candidate["related_recommendation_action"], "monitor_or_accumulate")
        self.assertEqual(candidate["related_recommended_weight"], 0.05)
        self.assertEqual(candidate["links"]["thesis"], "/theses/thesis-7001")
        self.assertEqual(candidate["links"]["recommendation"], "/recommendations/recommendation-7101")
        self.assertFalse(candidate["automatic_order_allowed"])
        self.assertFalse(candidate["broker_submit_allowed"])
        self.assertEqual(candidate["order_boundary"], "read_only_no_order")

    def test_portfolio_position_sizing_context_sql_is_read_only_professional_context(self) -> None:
        sql = render_frontend_portfolio_position_sizing_context_state_sql(
            portfolio_name="Long Term Paper",
            snapshot_date=date(2026, 5, 26),
        )

        self.assertTrue(sql.startswith("-- frontend portfolio position sizing context lookup"))
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("research.equity_research_artifact", sql)
        self.assertIn("signal.recommendation_score_component", sql)
        self.assertIn("'fundamental_quality_score'", sql)
        self.assertIn("'valuation_margin_score'", sql)
        self.assertNotIn("insert into", sql.lower())
        self.assertNotIn("update ", sql.lower())
        self.assertNotIn("delete from", sql.lower())

    def test_live_portfolio_coverage_returns_empty_state_when_snapshot_is_missing(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-20",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=EmptyPortfolioCoverageExecutor(),
            generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2026-05-20")
        self.assertEqual(payload["data"]["summary"]["position_count"], 0)
        self.assertEqual(payload["data"]["risk_budget"]["status"], "missing_position_snapshot")
        self.assertEqual(payload["data"]["risk_budget"]["concentration"]["status"], "missing_position_snapshot")
        self.assertEqual(payload["data"]["risk_budget"]["rebalance_priorities"], [])
        self.assertEqual(
            payload["data"]["risk_budget"]["review_reasons"],
            ["position_snapshot_missing"],
        )
        self.assertEqual(payload["data"]["positions"], [])
        self.assertFalse(payload["data"]["attribution_readiness"]["is_ready"])
        self.assertEqual(
            payload["data"]["attribution_readiness"]["blocking_reasons"],
            ["missing_position_snapshot:Long Term Paper"],
        )

    def test_live_portfolio_coverage_flags_sector_theme_concentration(self) -> None:
        payload = resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=ConcentratedPortfolioCoverageExecutor(),
            generated_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )

        risk_budget = payload["data"]["risk_budget"]
        self.assertEqual(risk_budget["status"], "needs_position_review")
        self.assertEqual(risk_budget["concentration"]["status"], "needs_concentration_review")
        self.assertEqual(risk_budget["concentration"]["over_limit_count"], 2)
        self.assertIn("sector_over_limit:TECHNOLOGY", risk_budget["review_reasons"])
        self.assertIn("theme_over_limit:AI_SEMICONDUCTOR_CYCLE", risk_budget["review_reasons"])
        concentration_priority = [
            item for item in risk_budget["rebalance_priorities"]
            if item["action"] == "review_sector_theme_concentration"
        ]
        self.assertEqual(concentration_priority[0]["symbol"], "AAPL")
        self.assertEqual(concentration_priority[0]["order_boundary"], "read_only_no_order")

    def test_live_portfolio_concentration_sql_reads_sector_membership(self) -> None:
        sql = render_frontend_portfolio_concentration_state_sql(
            portfolio_name="Long Term Paper",
            snapshot_date=date(2026, 5, 23),
        )

        self.assertIn("portfolio.position_snapshot", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("ref.classification_node", sql)
        self.assertIn("when node.node_type = 'sector' then 'sector'", sql)
        self.assertIn("sector_exposure_rows", sql)
        self.assertIn("'sector_exposures'", sql)

    def test_live_portfolio_coverage_falls_back_to_latest_snapshot_before_requested_date(self) -> None:
        executor = LatestPortfolioCoverageExecutor()
        payload = resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-20",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
            generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
        )

        self.assertEqual(payload["contract_version"], "frontend-api-v0.1")
        self.assertEqual(payload["data"]["as_of_date"], "2026-05-19")
        self.assertEqual(payload["data"]["summary"]["position_count"], 1)
        self.assertEqual(payload["data"]["summary"]["weight_coverage_ratio"], 1.0)
        self.assertEqual(payload["data"]["positions"][0]["symbol"], "SPY")
        self.assertEqual(payload["data"]["risk_budget"]["largest_position_symbol"], "SPY")
        self.assertEqual(payload["data"]["attribution_readiness"]["blocking_reasons"], [])
        self.assertTrue(any(sql.startswith("-- frontend latest portfolio snapshot date lookup") for sql in executor.scalar_sql))

    def test_live_portfolio_coverage_allows_explicit_measurement_end_date(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01&measurementEndDate=2024-12-02",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
        )
        self.assertTrue(
            any(
                sql.startswith("-- portfolio outcome coverage report") and "2024-12-02" in sql
                for sql in executor.scalar_sql
            )
        )

    def test_live_collection_sql_reads_are_bounded_by_page_window(self) -> None:
        cursor = encode_frontend_cursor(10)
        cases = (
            "/api/stocks?limit=5",
            "/api/paper-trading/preview?limit=5",
            "/api/events?asOfDate=2024-11-01&limit=5",
            "/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02&limit=5",
            f"/api/remediation-tickets?status=open&limit=5&cursor={cursor}",
            f"/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01&limit=5&cursor={cursor}",
        )

        for path in cases:
            with self.subTest(path=path):
                executor = FakeLiveExecutor()
                resolve_live_frontend_response(
                    path,
                    config=type("Config", (), {"psql_command": "psql"})(),
                    executor=executor,
                )

                page_sql = next((sql for sql in executor.scalar_sql if "limit 6" in sql), "")
                self.assertIn("limit 6", page_sql)
                if "cursor=" in path:
                    self.assertIn("offset 10", page_sql)

    def test_live_adapter_rejects_unsupported_path(self) -> None:
        with self.assertRaises(FrontendLiveUnsupportedPathError):
            resolve_live_frontend_response(
                "/api/scheduler/runs",
                config=type("Config", (), {"psql_command": "psql"})(),
                executor=FakeLiveExecutor(),
            )

    def test_live_adapter_requires_psql_command_without_injected_executor(self) -> None:
        with self.assertRaises(FrontendLiveUnavailableError):
            resolve_live_frontend_response(
                "/api/remediation-tickets?status=open",
                config=type("Config", (), {"psql_command": None})(),
            )


if __name__ == "__main__":
    unittest.main()
