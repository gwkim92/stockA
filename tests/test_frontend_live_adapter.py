from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from stockanalysis.frontend.live_adapter import (
    FrontendLiveUnavailableError,
    FrontendLiveUnsupportedPathError,
    render_frontend_ai_evidence_detail_state_sql,
    render_frontend_cycle_state_list_sql,
    render_frontend_thesis_detail_state_sql,
    resolve_live_frontend_response,
)


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
                            "latest_status": "succeeded",
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
                            "quality_gate": "human_review_required",
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
                            "component": "cycle_state",
                            "value": "0.7400",
                            "weight": "0.3500",
                            "evidence_id": "cycle-state-ANNUAL_REPORTING-20241101",
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
        if sql.startswith("-- portfolio outcome coverage lookup"):
            return json.dumps(
                [
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "market_value": "2229.10",
                        "position_weight": "0.0500",
                        "linked_thesis_id": 7001,
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "outcome_id": 8101,
                        "outcome_status": "working",
                        "success_grade": "pass",
                        "coverage_status": "covered",
                    },
                    {
                        "portfolio_id": 3001,
                        "portfolio_name": "Long Term Paper",
                        "snapshot_date": "2024-11-01",
                        "measurement_end_date": "2024-12-02",
                        "instrument_id": 502,
                        "primary_symbol": "BABA",
                        "market_value": "298.50",
                        "position_weight": "0.0300",
                        "linked_thesis_id": None,
                        "thesis_title": None,
                        "outcome_id": None,
                        "outcome_status": None,
                        "success_grade": None,
                        "coverage_status": "missing_thesis",
                    },
                ]
            )
        raise AssertionError(f"Unexpected SQL: {sql}")


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
        self.assertEqual(payload["data"]["scheduler"]["install_status"], "not_installed")
        self.assertEqual(
            payload["data"]["scheduler"]["runtime_env_readiness"],
            "template_rendered_placeholder_pending",
        )
        self.assertEqual(payload["data"]["freshness"][0]["dataset"], "market.daily_price_bar")
        self.assertEqual(payload["data"]["freshness"][0]["latest_observation_date"], "2024-12-02")
        self.assertIn("auth_rbac", payload["data"]["open_gates"])
        self.assertEqual(payload["links"]["dashboard"], "/api/dashboard/today")

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
        self.assertEqual(payload["data"]["score_components"][0]["component"], "cycle_state")
        self.assertEqual(payload["data"]["score_components"][0]["value"], 0.74)
        self.assertEqual(payload["data"]["linked_thesis_id"], "thesis-7001")
        self.assertEqual(payload["data"]["outcome"]["alpha"], 0.06)
        self.assertEqual(payload["links"]["thesis"], "/api/theses/thesis-7001")
        self.assertNotIn("source_event", payload["links"])

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
        self.assertEqual(payload["data"]["evidence"][0]["evidence_id"], "event-9001")
        self.assertEqual(payload["data"]["evidence"][1]["evidence_id"], "performance-outcome-8101")
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
        self.assertEqual(
            payload["links"]["source_document"],
            "/api/source-documents/aapl-2024-10k-20240928",
        )

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
        self.assertIn("event.event_document_link", ai_evidence_sql)
        self.assertIn("output_json #>> '{event,title}'", ai_evidence_sql)

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

    def test_live_portfolio_coverage_allows_explicit_measurement_end_date(self) -> None:
        executor = FakeLiveExecutor()
        resolve_live_frontend_response(
            "/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01&measurementEndDate=2024-12-02",
            config=type("Config", (), {"psql_command": "psql"})(),
            executor=executor,
        )
        self.assertIn("2024-12-02", executor.scalar_sql[-1])

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
