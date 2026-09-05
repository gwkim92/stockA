import { RecommendationExecutiveBrief } from "@/components/recommendation-executive-brief";
import { RecommendationPositionReality } from "@/components/recommendation-position-reality";
import { getRecommendationDetail } from "@/lib/frontend-api";
import { loadRecommendationThesis } from "@/lib/recommendation-memo-data";
import { memoPositionLabel } from "@/lib/recommendation-memo-model";
import { koCode } from "@/lib/korean-labels";
import { buildRecommendationViewModel, recommendationProductKind } from "@/lib/presentation";

import { RecommendationCompatibilityReport } from "./_components/RecommendationCompatibilityReport";
import { RecommendationDecisionHeader } from "./_components/RecommendationDecisionHeader";
import { RecommendationDecisionWaterfall } from "./_components/RecommendationDecisionFlowPanels";
import { RecommendationMarketCorrelationsPanel } from "./_components/RecommendationMarketCorrelationsPanel";
import { RecommendationProfessionalDetailSections } from "./_components/RecommendationProfessionalDetailSections";
import { RecommendationQualityBoundaryPanel } from "./_components/RecommendationQualityBoundaryPanel";
import { recommendationEvidenceTraceCards } from "./_components/recommendation-evidence-trace-model";
import { userFacingRecommendationText } from "./_components/recommendation-panel-format";
import {
  hasProfessionalRecommendationDetail,
  recommendationDecisionCopy,
  recommendationOrderBoundaryLabel,
  recommendationProductProfile,
} from "./_components/recommendation-product-model";
import {
  recommendationImmediateFocus,
  recommendationQualityChecks,
  recommendationQualityDecision,
} from "./_components/recommendation-quality-model";
import {
  brokerComponents,
  cycleStackComponents,
  fundamentalComponents,
  macroFlowRows,
} from "./_components/recommendation-score-component-model";
import { recommendationWaterfallCards } from "./_components/recommendation-waterfall-model";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천 상세" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;
  if (!hasProfessionalRecommendationDetail(data)) {
    return <RecommendationCompatibilityReport data={data} />;
  }
  const linkedThesis = await loadRecommendationThesis(data);
  const qualityDecision = recommendationQualityDecision(data);
  const qualityChecks = recommendationQualityChecks(data);
  const traceCards = recommendationEvidenceTraceCards(data);
  const macroFlowComponents = data.score_components.filter((component) => macroFlowRows(component).length > 0);
  const cycleStack = cycleStackComponents(data.score_components);
  const fundamentalStack = fundamentalComponents(data.score_components);
  const brokerStack = brokerComponents(data.score_components);
  const financialStatementModel = data.financial_statement_model;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const sourceBlocked = data.professional_evidence_audit.source_blocker.blocked === true
    || data.professional_source_guardrail?.blocked === true
    || data.professional_decision_waterfall.status === "source_data_blocked";
  const decisionWaterfall = sourceBlocked
    ? { ...data.professional_decision_waterfall, paper_validation_input_allowed: false }
    : data.professional_decision_waterfall;
  const professionalAudit = data.professional_evidence_audit;
  const productProfile = recommendationProductProfile(data);
  const recommendationProduct = recommendationProductKind(data);
  const recommendationViewModel = buildRecommendationViewModel(data);
  const readyDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "ready").length;
  const watchDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "watch" || step.tone === "neutral").length;
  const blockedDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "blocked").length;
  const marketCorrelationCount = data.market_correlations.length;
  const positionStatusLabel = memoPositionLabel(data.position_context.status);
  const waterfallCards = recommendationWaterfallCards({
    data,
    productProfile,
    cycleStack,
    macroFlowComponents,
    qualityDecision,
    decisionWaterfall,
    professionalAudit,
    outcomeMeasured,
  });
  const immediateFocusItems = recommendationImmediateFocus({
    data,
    productProfile,
    qualityDecision,
    decisionWaterfall,
    professionalAudit,
    blockedDecisionStepCount,
    watchDecisionStepCount,
    outcomeMeasured,
    marketCorrelationCount,
    macroFlowComponents,
    fundamentalStack,
  });

  return (
    <div className="pageStack">
      <RecommendationDecisionHeader
        symbol={data.symbol}
        asOfDate={data.as_of_date}
        horizonLabel={koCode(data.horizon_type)}
        recommendationLabel={koCode(data.recommendation)}
        positionStatusLabel={positionStatusLabel}
        productKind={recommendationProduct}
        viewModel={recommendationViewModel}
        counts={{
          readyStepCount: readyDecisionStepCount,
          watchStepCount: watchDecisionStepCount,
          blockedStepCount: blockedDecisionStepCount,
          totalStepCount: decisionWaterfall.steps.length,
          marketCorrelationCount,
          financialMetricCount: financialStatementModel.computed_metric_count,
          fundHoldingCount: data.fund_instrument_analysis?.holding_count ?? null,
        }}
        execution={{
          paperValidationAllowed: decisionWaterfall.paper_validation_input_allowed,
          brokerSubmitAllowed: decisionWaterfall.broker_submit_allowed,
          orderStatusLabel: recommendationOrderBoundaryLabel(decisionWaterfall.order_boundary),
        }}
      />

      <RecommendationExecutiveBrief data={data} thesis={linkedThesis} />

      <RecommendationPositionReality data={data} />

      <RecommendationDecisionWaterfall
        data={data}
        cards={waterfallCards}
        {...(immediateFocusItems[0] ? { focusItem: immediateFocusItems[0] } : {})}
        qualityDecision={qualityDecision}
        decisionWaterfall={decisionWaterfall}
      />

      <RecommendationQualityBoundaryPanel
        boundary={{
          summary: userFacingRecommendationText(decisionWaterfall.summary),
          status: recommendationDecisionCopy(decisionWaterfall.status),
          asOfDate: decisionWaterfall.as_of_date,
          readyStepCount: readyDecisionStepCount,
          watchStepCount: watchDecisionStepCount,
          blockedStepCount: blockedDecisionStepCount,
          totalStepCount: decisionWaterfall.steps.length,
          paperValidationInputAllowed: decisionWaterfall.paper_validation_input_allowed,
          automaticOrderAllowed: decisionWaterfall.automatic_order_allowed,
          brokerSubmitAllowed: decisionWaterfall.broker_submit_allowed,
          orderBoundaryLabel: recommendationOrderBoundaryLabel(decisionWaterfall.order_boundary),
        }}
        qualityChecks={qualityChecks}
        qualityDecision={qualityDecision}
      />

      <RecommendationMarketCorrelationsPanel symbol={data.symbol} correlations={data.market_correlations} />

      <RecommendationProfessionalDetailSections
        data={data}
        isCompany={productProfile.kind === "company"}
        qualityDecision={qualityDecision}
        scoreStacks={{
          brokerStack,
          cycleStack,
          fundamentalStack,
          macroFlowComponents,
        }}
        traceCards={traceCards}
      />
    </div>
  );
}
