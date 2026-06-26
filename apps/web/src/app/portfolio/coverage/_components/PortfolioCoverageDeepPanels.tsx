import type { PortfolioCoverageData, TradingReadinessData } from "@/lib/types";

import { PortfolioConcentrationPanels } from "./PortfolioConcentrationPanels";
import { PortfolioDecisionFeedbackPanels } from "./PortfolioDecisionFeedbackPanels";
import { PortfolioOutcomeCadencePanels } from "./PortfolioOutcomeCadencePanels";
import { PortfolioRebalancePanels } from "./PortfolioRebalancePanels";
import { PortfolioRiskBudgetPanels } from "./PortfolioRiskBudgetPanels";

type PortfolioCoverageDeepPanelsProps = {
  readonly benchmarkActiveShare: number | null;
  readonly benchmarkCode: string;
  readonly benchmarkDriftCalculated: boolean;
  readonly benchmarkSource: string;
  readonly data: PortfolioCoverageData;
  readonly riskGuardrail: TradingReadinessData["portfolio_risk_budget_guardrail"];
};

export function PortfolioCoverageDeepPanels({
  benchmarkActiveShare,
  benchmarkCode,
  benchmarkDriftCalculated,
  benchmarkSource,
  data,
  riskGuardrail,
}: PortfolioCoverageDeepPanelsProps) {
  const riskBudget = data.risk_budget;

  return (
    <>
      <PortfolioRiskBudgetPanels
        allocationPolicy={data.allocation_policy}
        benchmarkActiveShare={benchmarkActiveShare}
        benchmarkCode={benchmarkCode}
        benchmarkDriftCalculated={benchmarkDriftCalculated}
        benchmarkSource={benchmarkSource}
        riskBudget={riskBudget}
        riskGuardrail={riskGuardrail}
      />
      <PortfolioDecisionFeedbackPanels
        reviewFeedback={riskBudget.review_decision_feedback}
        reviewHistory={riskBudget.review_decision_history}
      />
      <PortfolioOutcomeCadencePanels
        reviewActionRouter={riskBudget.review_feedback_action_router}
        reviewCadence={riskBudget.review_feedback_cadence}
        reviewCalibration={riskBudget.review_feedback_calibration}
      />
      <PortfolioRebalancePanels
        benchmarkCode={benchmarkCode}
        benchmarkSource={benchmarkSource}
        candidateReview={riskBudget.rebalance_candidate_review}
        positionSizingReview={riskBudget.position_sizing_review}
      />
      <PortfolioConcentrationPanels concentration={riskBudget.concentration} riskBudget={riskBudget} />
    </>
  );
}
