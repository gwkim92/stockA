from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from stockanalysis.frontend.live_adapter import (
    FrontendLiveUnavailableError,
    FrontendLiveUnsupportedPathError,
    is_live_supported_path,
    render_frontend_ai_news_cluster_list_state_sql,
    render_frontend_ai_evidence_detail_state_sql,
    render_frontend_cycle_state_list_sql,
    render_frontend_event_list_state_sql,
    render_frontend_paper_trading_preview_state_sql,
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
                    "open_gates": [
                        "production_api_server",
                        "auth_rbac",
                        "alert_destination",
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
                    "recent_events": [
                        {
                            "event_id": 9001,
                            "title": "AAPL 2024 10-K annual reporting event",
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
                        "이 화면은 가상 거래(Paper) 미리보기이며 실제 주문을 만들지 않는다.",
                        "모든 가상 조치는 사람 승인 전까지 실행되지 않는다.",
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
        if sql.startswith("-- frontend event list state lookup"):
            return json.dumps(
                {
                    "as_of_date": "2024-11-01",
                    "summary": {
                        "event_count": 1,
                        "ai_extracted_count": 1,
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
                            "quality_gate": "human_review_required",
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
                        }
                    ],
                    "linked_thesis_id": 7001,
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
                                "quality_status": "ready_for_human_review",
                                "primary_evidence_id": "ai-evidence-8801",
                            },
                            "outcome": {
                                "measurement_end_date": "2024-12-02",
                                "label": "outperform",
                                "alpha": "0.0600",
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
                                "quality_status": "blocked",
                                "primary_evidence_id": None,
                            },
                            "outcome": {
                                "measurement_end_date": None,
                                "label": "unmeasured",
                                "alpha": None,
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
                    "evidence": [
                        {
                            "evidence_id": 9001,
                            "type": "source_document_event",
                            "title": "AAPL 2024 10-K annual reporting event",
                        },
                        {
                            "evidence_id": 8101,
                            "type": "performance_outcome",
                            "title": "AAPL outperformed SPY over measurement window",
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
                            "quality_gate": "human_review_required",
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
                            "quality_gate": "human_review_required",
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
                        "quality_gate": "human_review_required",
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
        return super().execute_scalar(sql)


class FrontendLiveAdapterTests(unittest.TestCase):
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

    def test_live_data_health_response_matches_frontend_contract_shape(self) -> None:
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
        self.assertEqual(payload["data"]["freshness"][0]["dataset"], "market.daily_price_bar")
        self.assertEqual(payload["data"]["freshness"][0]["latest_observation_date"], "2024-12-02")
        self.assertIn("auth_rbac", payload["data"]["open_gates"])
        self.assertEqual(payload["data"]["provider_budget"]["status"], "not_configured")
        self.assertEqual(payload["data"]["provider_budget"]["provider"], "alpha_vantage")
        self.assertEqual(payload["data"]["manual_local_ingest_smoke"]["status"], "not_configured")
        self.assertEqual(payload["data"]["manual_local_ingest_smoke"]["source"], "not_configured")
        self.assertEqual(payload["data"]["local_ingest_worker"]["status"], "not_configured")
        self.assertEqual(payload["data"]["local_ingest_worker"]["source"], "not_configured")
        self.assertEqual(payload["links"]["dashboard"], "/api/dashboard/today")

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
        self.assertIn("health_status in ('missing', 'stale', 'failed')", sql)
        self.assertIn("expected.job_id = 'portfolio-attribution-monthly'", sql)
        self.assertIn("then 'not_due'", sql)
        self.assertIn("'data_operations_artifact_runner'", sql)

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
        self.assertEqual(data["instrument"]["instrument_id"], "instrument-501")
        self.assertEqual(data["themes"][0]["theme_key"], "ANNUAL_REPORTING")
        self.assertEqual(data["theme_edges"][0]["relation_type"], "contains")
        self.assertEqual(data["events"][0]["event_id"], "event-9001")
        self.assertEqual(data["events"][0]["source_document_id"], "source-document-aapl-2024-10k-20240928")
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
        self.assertEqual(cluster["evidence_id"], "ai-evidence-2")
        self.assertEqual(cluster["theme_key"], "AI_SEMICONDUCTOR_CYCLE")
        self.assertEqual(cluster["symbols"], ["NVDA"])
        self.assertEqual(cluster["event_count"], 10)
        self.assertEqual(cluster["extraction_run"]["provider"], "local_rules")
        self.assertEqual(cluster["extraction_run"]["estimated_cost_usd"], 0.0)
        self.assertEqual(cluster["chunk_count"], 2)
        self.assertEqual(cluster["embedded_chunk_count"], 2)
        self.assertEqual(cluster["events"][0]["event_id"], "event-20")
        self.assertEqual(
            cluster["source_documents"][0]["source_document_id"],
            "rss:ai-semiconductor-cycle:65353569b9948d8593917bae",
        )
        self.assertNotIn("vector_storage_uri", json.dumps(data))
        self.assertNotIn("secret://", json.dumps(data))
        self.assertTrue(is_live_supported_path("/api/ai/news-clusters?asOfDate=2026-05-19"))

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
        self.assertIn("raw_recent_events as", detail_sql)
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
        self.assertEqual(payload["data"]["gate_summary"]["blocked_count"], 2)
        self.assertEqual(payload["data"]["broker_boundary"]["broker_code"], "simulated_paper")
        self.assertFalse(payload["data"]["broker_boundary"]["secret_configured"])
        self.assertEqual(payload["data"]["account_permission"]["permission_scope"], "paper_trade")
        self.assertEqual(payload["data"]["order_limit_policy"]["max_single_order_notional"], 50000.0)
        self.assertTrue(payload["data"]["kill_switches"][0]["is_engaged"])
        self.assertEqual(payload["data"]["paper_validation"]["conflict_count"], 1)
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
        self.assertEqual(payload["data"]["summary"]["event_count"], 1)
        self.assertEqual(payload["data"]["summary"]["ai_extracted_count"], 1)
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
        self.assertEqual(payload["data"]["linked_thesis_id"], "thesis-7001")
        review = payload["data"]["evidence_review"]
        self.assertEqual(review["quality_status"], "ready_for_human_review")
        self.assertEqual(review["summary"]["score_component_count"], 4)
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
        self.assertEqual(payload["pagination"]["limit"], 1)
        self.assertTrue(payload["pagination"]["has_more"])
        row = payload["data"]["recommendations"][0]
        self.assertEqual(row["recommendation_id"], "recommendation-7101")
        self.assertEqual(row["symbol"], "AAPL")
        self.assertEqual(row["instrument_id"], "instrument-501")
        self.assertEqual(row["score"], 0.78)
        self.assertEqual(row["recommended_weight"], 0.05)
        self.assertEqual(row["linked_thesis_id"], "thesis-7001")
        self.assertEqual(row["evidence"]["quality_status"], "ready_for_human_review")
        self.assertEqual(row["evidence"]["primary_evidence_id"], "ai-evidence-8801")
        self.assertEqual(row["outcome"]["alpha"], 0.06)
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
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("event.event_instrument_impact", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("'ready_for_human_review'", sql)
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
        self.assertIn("score_component_rows as", sql)
        self.assertIn("ai.extraction_artifact", sql)
        self.assertIn("'ai-evidence-' || artifact_id::text", sql)
        self.assertIn("'event-' || event_id::text", sql)
        self.assertIn("'return_since_first_observation'", sql)
        self.assertIn("'return_1d'", sql)
        self.assertIn("'universe-rank-' || lower(recommendation.primary_symbol)", sql)
        self.assertIn("'provenance', provenance", sql)
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
        self.assertEqual(payload["data"]["evidence"][0]["evidence_id"], "event-9001")
        self.assertEqual(payload["data"]["evidence"][1]["evidence_id"], "performance-outcome-8101")
        review = payload["data"]["evidence_review"]
        self.assertEqual(review["quality_status"], "ready_for_human_review")
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
        self.assertIn("투자 논리는 주문이 아니라 추천, 사이클, 가격 근거", thesis_sql)
        self.assertIn("event.event_document_link", ai_evidence_sql)
        self.assertIn("output_json #>> '{event,title}'", ai_evidence_sql)
        self.assertIn("then (select artifact_type from selected_artifact)", ai_evidence_sql)
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
        self.assertIn("document_instrument", event_sql)
        self.assertIn("coalesce(instrument.primary_symbol, document_instrument.primary_symbol)", event_sql)
        self.assertIn("artifact.event_id = event_row.event_id", theme_sql)
        self.assertIn("artifact.document_id = source_document.document_id", theme_sql)
        self.assertIn("('event-' || event_row.event_id::text) =", ai_evidence_sql)
        self.assertIn("document.external_document_id = regexp_replace", ai_evidence_sql)
        self.assertIn("from selected_event_candidates candidate", ai_evidence_sql)
        self.assertIn("where impact.event_id = candidate.event_id", ai_evidence_sql)
        self.assertIn("document.external_document_id = regexp_replace", source_document_sql)

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
        self.assertEqual(payload["data"]["positions"][0]["active_thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["positions"][0]["outcome_status"], "measured")
        self.assertEqual(payload["data"]["positions"][1]["action"], "needs_thesis_review")
        self.assertEqual(payload["data"]["attribution_readiness"]["blocking_reasons"], ["missing_thesis:BABA"])

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
        self.assertEqual(payload["data"]["positions"], [])
        self.assertFalse(payload["data"]["attribution_readiness"]["is_ready"])
        self.assertEqual(
            payload["data"]["attribution_readiness"]["blocking_reasons"],
            ["missing_position_snapshot:Long Term Paper"],
        )

    def test_live_portfolio_coverage_allows_explicit_measurement_end_date(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01&measurementEndDate=2024-12-02",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
        )
        self.assertIn("2024-12-02", executor.scalar_sql[-1])

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

                self.assertIn("limit 6", executor.scalar_sql[-1])
                if "cursor=" in path:
                    self.assertIn("offset 10", executor.scalar_sql[-1])

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
