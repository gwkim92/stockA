import type { DataHealthData } from "@/lib/types";

import { DataHealthBenchmarkDriftSection } from "./DataHealthBenchmarkDriftSection";
import { DataHealthOutcomeSections } from "./DataHealthOutcomeSections";
import { DataHealthPortfolioReviewCalibrationSection } from "./DataHealthPortfolioReviewCalibrationSection";
import { DataHealthPortfolioReviewCadenceSections } from "./DataHealthPortfolioReviewCadenceSections";
import { DataHealthPortfolioReviewHistorySections } from "./DataHealthPortfolioReviewHistorySections";
import { DataHealthProfessionalDepthSections } from "./DataHealthProfessionalDepthSections";
import { DataHealthProfessionalOverviewSections } from "./DataHealthProfessionalOverviewSections";
import {
  DEFAULT_BENCHMARK_DRIFT_QUALITY,
  DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR,
  DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK,
  DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE,
  DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION,
  DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH,
  DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION,
  DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY,
  DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT,
  DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION,
  DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION,
  DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER,
  DEFAULT_RECOMMENDATION_OUTCOME_MATURITY,
  DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS,
} from "./dataHealthModel";

type DataHealthInvestmentQualityDetailsProps = {
  readonly data: DataHealthData;
};

export function DataHealthInvestmentQualityDetails({ data }: DataHealthInvestmentQualityDetailsProps) {
  const outcomeWaitMonitor =
    data.outcome_maturity_wait_monitor ?? DEFAULT_OUTCOME_MATURITY_WAIT_MONITOR;
  const outcomeCalibration =
    data.recommendation_outcome_calibration ?? DEFAULT_RECOMMENDATION_OUTCOME_CALIBRATION;
  const outcomeMaturity = data.recommendation_outcome_maturity ?? DEFAULT_RECOMMENDATION_OUTCOME_MATURITY;
  const outcomeDueActionRouter =
    data.recommendation_outcome_due_action_router ?? DEFAULT_RECOMMENDATION_OUTCOME_DUE_ACTION_ROUTER;
  const weightReviewReadiness =
    data.recommendation_weight_review_readiness ?? DEFAULT_RECOMMENDATION_WEIGHT_REVIEW_READINESS;
  const professionalQuality =
    data.professional_analysis_quality ?? DEFAULT_PROFESSIONAL_ANALYSIS_QUALITY;
  const professionalRecommendationAudit =
    data.professional_recommendation_coverage_audit ?? DEFAULT_PROFESSIONAL_RECOMMENDATION_COVERAGE_AUDIT;
  const professionalNextAction =
    data.professional_analysis_next_action ?? DEFAULT_PROFESSIONAL_ANALYSIS_NEXT_ACTION;
  const professionalDepth =
    data.professional_analysis_depth ?? DEFAULT_PROFESSIONAL_ANALYSIS_DEPTH;
  const professionalSourceGaps =
    data.professional_source_gap_prioritization ?? DEFAULT_PROFESSIONAL_SOURCE_GAP_PRIORITIZATION;
  const benchmarkDriftQuality = data.benchmark_drift_quality ?? DEFAULT_BENCHMARK_DRIFT_QUALITY;
  const benchmarkDriftDecisionBySymbol = new Map(
    benchmarkDriftQuality.outlier_decisions.map((decision) => [decision.symbol, decision]),
  );
  const portfolioReviewHistory =
    data.portfolio_review_decision_history ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_HISTORY;
  const portfolioReviewFeedback =
    data.portfolio_review_decision_feedback ?? DEFAULT_PORTFOLIO_REVIEW_DECISION_FEEDBACK;
  const portfolioReviewCalibration =
    data.portfolio_review_feedback_calibration ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CALIBRATION;
  const portfolioReviewCadence =
    data.portfolio_review_feedback_cadence ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_CADENCE;
  const portfolioReviewActionRouter =
    data.portfolio_review_feedback_action_router ?? DEFAULT_PORTFOLIO_REVIEW_FEEDBACK_ACTION_ROUTER;

  return (
    <details className="operator-details-panel reveal delay-2" id="investment-quality-details">
      <summary>
        <span>투자 품질·성과 상세</span>
        <strong>성과검증, 전문 분석, 포트폴리오 검토 기록</strong>
      </summary>
      <div className="details-inner">
        <DataHealthOutcomeSections
          outcomeWaitMonitor={outcomeWaitMonitor}
          outcomeCalibration={outcomeCalibration}
          outcomeMaturity={outcomeMaturity}
          outcomeDueActionRouter={outcomeDueActionRouter}
          weightReviewReadiness={weightReviewReadiness}
        />
        <DataHealthProfessionalOverviewSections
          professionalQuality={professionalQuality}
          professionalRecommendationAudit={professionalRecommendationAudit}
          professionalNextAction={professionalNextAction}
        />
        <DataHealthProfessionalDepthSections
          professionalDepth={professionalDepth}
          professionalSourceGaps={professionalSourceGaps}
        />
        <DataHealthBenchmarkDriftSection
          benchmarkDriftQuality={benchmarkDriftQuality}
          benchmarkDriftDecisionBySymbol={benchmarkDriftDecisionBySymbol}
        />
        <DataHealthPortfolioReviewHistorySections
          portfolioReviewHistory={portfolioReviewHistory}
          portfolioReviewFeedback={portfolioReviewFeedback}
        />
        <DataHealthPortfolioReviewCalibrationSection portfolioReviewCalibration={portfolioReviewCalibration} />
        <DataHealthPortfolioReviewCadenceSections
          portfolioReviewCadence={portfolioReviewCadence}
          portfolioReviewActionRouter={portfolioReviewActionRouter}
        />
      </div>
    </details>
  );
}
