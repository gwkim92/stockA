from __future__ import annotations

import unittest
from datetime import datetime, timezone

from stockanalysis.operations.cadence import (
    DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
    build_data_operations_cadence_report,
    list_data_operation_cadences,
    render_data_operations_expected_jobs_sql_values,
)


class DataOperationsCadenceTests(unittest.TestCase):
    def test_cadence_report_exposes_intraday_daily_weekly_monthly_jobs(self) -> None:
        report = build_data_operations_cadence_report(
            generated_at=datetime(2026, 5, 3, tzinfo=timezone.utc),
        )

        self.assertEqual(report["report_name"], "data_operations_cadence_foundation")
        self.assertEqual(report["generated_at"], "2026-05-03T00:00:00Z")
        self.assertEqual(report["artifact_root_env"], DATA_OPERATIONS_ARTIFACT_ROOT_ENV)
        self.assertEqual(report["activation_status"], "reference_only_not_scheduled")
        self.assertGreaterEqual(report["cadence_counts"]["intraday"], 3)
        self.assertGreaterEqual(report["cadence_counts"]["daily"], 3)
        self.assertGreaterEqual(report["cadence_counts"]["weekly"], 3)
        self.assertGreaterEqual(report["cadence_counts"]["monthly"], 2)
        universe_job = next(job for job in report["jobs"] if job["job_id"] == "market-universe-weekly")
        self.assertEqual(universe_job["pipeline_name"], "market_universe_bootstrap")
        self.assertIn("market-universe-bootstrap", universe_job["command_template"])
        self.assertIn("sec_identity", universe_job["required_env_groups"])
        market_job = next(job for job in report["jobs"] if job["job_id"] == "market-price-daily")
        self.assertIn("stockanalysis-operations market-price-daily-run", market_job["command_template"])
        self.assertIn("--skip-if-fresh", market_job["command_template"])
        self.assertIn("market_price_provider", market_job["required_env_groups"])
        news_job = next(job for job in report["jobs"] if job["job_id"] == "news-rss-daily")
        self.assertEqual(news_job["pipeline_name"], "news_rss_upsert")
        self.assertEqual(news_job["domain"], "news")
        self.assertEqual(news_job["cadence"], "intraday")
        self.assertIn("news-rss-daily-run", news_job["command_template"])
        self.assertIn("news_rss_feed_config", news_job["required_env_groups"])
        self.assertEqual(news_job["data_health_dataset"], "ingest.source_document")
        bootstrap_job = next(job for job in report["jobs"] if job["job_id"] == "news-missing-instrument-bootstrap-intraday")
        self.assertEqual(bootstrap_job["pipeline_name"], "news_missing_instrument_bootstrap")
        self.assertIn("news-missing-instrument-bootstrap-run", bootstrap_job["command_template"])
        self.assertIn("sec_identity", bootstrap_job["required_env_groups"])
        self.assertEqual(bootstrap_job["data_health_dataset"], "ref.instrument")
        enrichment_job = next(job for job in report["jobs"] if job["job_id"] == "news-rss-enrichment-intraday")
        self.assertEqual(enrichment_job["pipeline_name"], "news_rss_event_enrichment")
        self.assertEqual(enrichment_job["cadence"], "intraday")
        translation_job = next(job for job in report["jobs"] if job["job_id"] == "news-korean-translation-intraday")
        self.assertEqual(translation_job["pipeline_name"], "news_rss_korean_translation")
        self.assertIn("news-rss-translation-run", translation_job["command_template"])
        self.assertIn("openai_or_llm_provider", translation_job["required_env_groups"])
        cycle_ai_job = next(job for job in report["jobs"] if job["job_id"] == "cycle-community-ai-summary-daily")
        self.assertEqual(cycle_ai_job["pipeline_name"], "cycle_community_ai_summary")
        self.assertEqual(cycle_ai_job["domain"], "ai")
        self.assertIn("cycle-community-ai-summary-v2-run", cycle_ai_job["command_template"])
        self.assertIn("openai_or_llm_provider", cycle_ai_job["required_env_groups"])
        equity_research_job = next(job for job in report["jobs"] if job["job_id"] == "equity-research-reporting-daily")
        self.assertEqual(equity_research_job["pipeline_name"], "equity_research_reporting")
        self.assertEqual(equity_research_job["domain"], "ai")
        self.assertIn("equity-research-reporting-run", equity_research_job["command_template"])
        self.assertIn("openai_or_llm_provider", equity_research_job["required_env_groups"])
        self.assertEqual(equity_research_job["data_health_dataset"], "research.equity_research_artifact")
        recommendation_quality_job = next(job for job in report["jobs"] if job["job_id"] == "recommendation-quality-eval-daily")
        self.assertEqual(recommendation_quality_job["pipeline_name"], "recommendation_quality_eval")
        self.assertEqual(recommendation_quality_job["domain"], "performance")
        self.assertIn("recommendation-quality-eval-run", recommendation_quality_job["command_template"])
        recommendation_fundamental_job = next(
            job for job in report["jobs"] if job["job_id"] == "recommendation-fundamental-components-daily"
        )
        self.assertEqual(recommendation_fundamental_job["pipeline_name"], "recommendation_fundamental_components")
        self.assertEqual(recommendation_fundamental_job["domain"], "fundamentals")
        self.assertIn("recommendation-fundamental-components-run", recommendation_fundamental_job["command_template"])
        self.assertEqual(recommendation_fundamental_job["data_health_dataset"], "signal.recommendation_score_component")
        financial_normalization_job = next(
            job for job in report["jobs"] if job["job_id"] == "financial-metric-normalization-weekly"
        )
        self.assertEqual(financial_normalization_job["pipeline_name"], "financial_metric_normalization")
        self.assertEqual(financial_normalization_job["domain"], "fundamentals")
        self.assertEqual(financial_normalization_job["cadence"], "weekly")
        self.assertIn("financial-metric-normalization-run", financial_normalization_job["command_template"])
        self.assertEqual(financial_normalization_job["data_health_dataset"], "market.financial_metric_normalized")
        peer_relative_job = next(job for job in report["jobs"] if job["job_id"] == "peer-relative-analysis-weekly")
        self.assertEqual(peer_relative_job["pipeline_name"], "peer_relative_analysis")
        self.assertEqual(peer_relative_job["domain"], "fundamentals")
        self.assertIn("peer-relative-analysis-run", peer_relative_job["command_template"])
        self.assertEqual(peer_relative_job["data_health_dataset"], "market.peer_relative_snapshot")
        forecast_job = next(job for job in report["jobs"] if job["job_id"] == "financial-forecast-inputs-weekly")
        self.assertEqual(forecast_job["pipeline_name"], "financial_forecast_inputs")
        self.assertEqual(forecast_job["domain"], "fundamentals")
        self.assertIn("financial-forecast-inputs-run", forecast_job["command_template"])
        self.assertEqual(forecast_job["data_health_dataset"], "market.financial_forecast_input")
        sotp_job = next(job for job in report["jobs"] if job["job_id"] == "sum-of-parts-valuation-weekly")
        self.assertEqual(sotp_job["pipeline_name"], "sum_of_parts_valuation")
        self.assertEqual(sotp_job["domain"], "fundamentals")
        self.assertIn("sum-of-parts-valuation-run", sotp_job["command_template"])
        self.assertEqual(sotp_job["data_health_dataset"], "market.sum_of_parts_component")
        valuation_job = next(job for job in report["jobs"] if job["job_id"] == "valuation-snapshot-weekly")
        self.assertEqual(valuation_job["pipeline_name"], "valuation_snapshot")
        self.assertEqual(valuation_job["domain"], "fundamentals")
        self.assertIn("valuation-snapshot-run", valuation_job["command_template"])
        self.assertEqual(valuation_job["data_health_dataset"], "market.valuation_snapshot")
        competitive_job = next(
            job for job in report["jobs"] if job["job_id"] == "industry-competitive-positioning-weekly"
        )
        self.assertEqual(competitive_job["pipeline_name"], "industry_competitive_positioning")
        self.assertEqual(competitive_job["domain"], "fundamentals")
        self.assertIn("industry-competitive-positioning-run", competitive_job["command_template"])
        self.assertEqual(competitive_job["data_health_dataset"], "research.industry_competitive_position")
        companyfacts_job = next(job for job in report["jobs"] if job["job_id"] == "sec-companyfacts-weekly")
        self.assertEqual(companyfacts_job["pipeline_name"], "sec_companyfacts_upsert")
        self.assertEqual(companyfacts_job["domain"], "sec")
        self.assertIn("sec-companyfacts-upsert", companyfacts_job["command_template"])
        self.assertEqual(companyfacts_job["data_health_dataset"], "market.financial_statement_period")
        recommendation_outcome_job = next(job for job in report["jobs"] if job["job_id"] == "recommendation-outcome-backfill-daily")
        self.assertEqual(recommendation_outcome_job["pipeline_name"], "performance_outcome_schedule_bootstrap")
        self.assertEqual(recommendation_outcome_job["domain"], "performance")
        self.assertIn("recommendation-outcome-backfill-run", recommendation_outcome_job["command_template"])
        self.assertIn("market_price_history", recommendation_outcome_job["required_env_groups"])
        performance_job = next(job for job in report["jobs"] if job["job_id"] == "performance-outcome-monthly")
        self.assertIn("recommendation-outcome-backfill-run", performance_job["command_template"])

    def test_cadence_filter_limits_jobs(self) -> None:
        jobs = list_data_operation_cadences(cadence="daily")

        self.assertTrue(jobs)
        self.assertTrue(all(job.cadence == "daily" for job in jobs))

    def test_intraday_cadence_filter_limits_jobs(self) -> None:
        jobs = list_data_operation_cadences(cadence="intraday")

        self.assertTrue(jobs)
        self.assertTrue(all(job.cadence == "intraday" for job in jobs))

    def test_expected_jobs_sql_values_are_safe_static_tuples(self) -> None:
        values_sql = render_data_operations_expected_jobs_sql_values()

        self.assertIn("'market_universe_bootstrap'", values_sql)
        self.assertIn("'news_rss_upsert'", values_sql)
        self.assertIn("'cycle_community_ai_summary'", values_sql)
        self.assertIn("'equity_research_reporting'", values_sql)
        self.assertIn("'recommendation_quality_eval'", values_sql)
        self.assertIn("'recommendation_fundamental_components'", values_sql)
        self.assertIn("'sec_companyfacts_upsert'", values_sql)
        self.assertIn("'financial_metric_normalization'", values_sql)
        self.assertIn("'peer_relative_analysis'", values_sql)
        self.assertIn("'valuation_snapshot'", values_sql)
        self.assertIn("'portfolio_remediation_daily_automation'", values_sql)
        self.assertIn("'performance_outcome_schedule_bootstrap'", values_sql)
        self.assertIn("'stdout_json_and_stderr_log'", values_sql)
        self.assertNotIn("STOCKANALYSIS_DATABASE_URL", values_sql)
        self.assertNotIn("Bearer", values_sql)


if __name__ == "__main__":
    unittest.main()
