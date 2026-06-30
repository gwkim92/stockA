import type { Route } from "next";

import { ProfessionalResearchFlow, type ResearchFlowStep } from "@/components/professional-research-flow";
import { RecommendationProfessionalAuditPanel } from "@/components/recommendation-professional-audit-panel";
import { RecommendationScoreAuditPanel } from "@/components/recommendation-score-audit-panel";
import { ValuationTargetRangeCard } from "@/components/valuation-target-range-card";
import type { RecommendationQualityDecision } from "@/components/recommendation-product-overview";
import type { RecommendationDetailData } from "@/lib/types";

import { RecommendationDetailDisclosure } from "./RecommendationDetailDisclosure";
import { RecommendationEquityResearchPanel } from "./RecommendationEquityResearchPanel";
import { RecommendationEvidenceReviewPanel } from "./RecommendationEvidenceReviewPanel";
import { RecommendationEvidenceTracePanel, type RecommendationEvidenceTraceCard } from "./RecommendationEvidenceTracePanel";
import { RecommendationFinancialStatementModelPanel } from "./RecommendationFinancialStatementModelPanel";
import { RecommendationFundInstrumentAnalysisPanel } from "./RecommendationFundInstrumentAnalysisPanel";
import { RecommendationIndustryCompetitivePositionPanel } from "./RecommendationIndustryCompetitivePositionPanel";
import { RecommendationMacroFlowPanel } from "./RecommendationMacroFlowPanel";
import { RecommendationScoreComponentPanels } from "./RecommendationScoreComponentPanels";
import {
  type ScoreComponent,
} from "./recommendation-score-component-model";
import {
  recommendationPanelOrderBoundaryLabel,
  userFacingRecommendationText,
} from "./recommendation-panel-format";

type ScoreStacks = {
  readonly brokerStack: readonly ScoreComponent[];
  readonly cycleStack: readonly ScoreComponent[];
  readonly fundamentalStack: readonly ScoreComponent[];
  readonly macroFlowComponents: readonly ScoreComponent[];
};

type RecommendationProfessionalDetailSectionsProps = {
  readonly data: RecommendationDetailData;
  readonly isCompany: boolean;
  readonly qualityDecision: RecommendationQualityDecision;
  readonly scoreStacks: ScoreStacks;
  readonly traceCards: readonly RecommendationEvidenceTraceCard[];
};

type ValuationSensitivityItem = {
  readonly key: string;
  readonly value: string;
};

function valuationSensitivityItems(value: Record<string, unknown>): readonly ValuationSensitivityItem[] {
  return Object.entries(value).map(([key, metricValue]) => ({
    key,
    value:
      typeof metricValue === "number"
        ? metricValue.toLocaleString("ko-KR")
        : typeof metricValue === "string" || typeof metricValue === "boolean" || metricValue === null || metricValue === undefined
          ? userFacingRecommendationText(metricValue)
          : JSON.stringify(metricValue),
  }));
}

function reviewCount(value: number | boolean | undefined) {
  if (typeof value === "number") {
    return value;
  }
  return value ? 1 : 0;
}

function recommendationRouteWithSymbol(href: string | null | undefined, symbol: string): Route | undefined {
  if (!href) {
    return undefined;
  }
  return href.replaceAll("UNKNOWN", encodeURIComponent(symbol)) as Route;
}

function researchFlowTone(tone: string): ResearchFlowStep["tone"] {
  if (tone === "ready") {
    return "ready";
  }
  if (tone === "blocked") {
    return "blocked";
  }
  return "watch";
}

function professionalResearchSteps(data: RecommendationDetailData): ResearchFlowStep[] {
  return data.professional_decision_waterfall.steps.map((step, index) => ({
    id: step.step_key,
    label: String(index + 1).padStart(2, "0"),
    title: userFacingRecommendationText(step.title),
    status: userFacingRecommendationText(step.status),
    tone: researchFlowTone(step.tone),
    body: `${userFacingRecommendationText(step.decision)}. ${userFacingRecommendationText(step.detail)}`,
    facts: step.facts.map((fact) => ({
      label: userFacingRecommendationText(fact.label),
      value: userFacingRecommendationText(fact.value),
    })),
    href: recommendationRouteWithSymbol(step.href, data.symbol),
    hrefLabel: step.href_label ? userFacingRecommendationText(step.href_label) : undefined,
  }));
}

export function RecommendationProfessionalDetailSections({
  data,
  isCompany,
  qualityDecision,
  scoreStacks,
  traceCards,
}: RecommendationProfessionalDetailSectionsProps) {
  const decisionWaterfall = data.professional_decision_waterfall;
  const professionalAudit = data.professional_evidence_audit;
  const financialStatementModel = data.financial_statement_model;
  const valuationTargetRange = data.valuation_target_range;
  const equityResearch = data.equity_research;
  const readyDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "ready").length;
  const watchDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "watch" || step.tone === "neutral").length;
  const blockedDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "blocked").length;
  const peerComponent = scoreStacks.fundamentalStack.find((component) => component.component === "peer_relative_score");
  const displayValuationTargetRange = {
    ...valuationTargetRange,
    summary: valuationTargetRange.summary.replaceAll("UNKNOWN", data.symbol),
  };
  const valuationItems = equityResearch ? valuationSensitivityItems(equityResearch.valuation_sensitivity) : [];
  const blockedEvidenceCount = reviewCount(data.evidence_review.summary.blocked_count);

  return (
    <>
      <RecommendationDetailDisclosure
        badge={`${readyDecisionStepCount}/${decisionWaterfall.steps.length} 단계`}
        eyebrow="심층 분석"
        id="recommendation-professional-flow"
        summary="전문 분석 흐름과 원천 감사는 추천을 채택하기 전에 필요한 경우 펼쳐서 대조한다."
        title={`${data.symbol} 추천의 전문 분석 경로`}
        tone={blockedDecisionStepCount > 0 ? "blocked" : watchDecisionStepCount > 0 ? "watch" : "ready"}
      >
        <ProfessionalResearchFlow
          eyebrow="전문 분석 흐름"
          title={`${data.symbol} 추천을 분석서처럼 읽는다`}
          summary={userFacingRecommendationText(decisionWaterfall.summary)}
          footer={`추천 산식 정책: ${userFacingRecommendationText(decisionWaterfall.score_policy)}. 실거래 상태: ${recommendationPanelOrderBoundaryLabel(decisionWaterfall.order_boundary)}.`}
          steps={professionalResearchSteps(data)}
        />
        <RecommendationProfessionalAuditPanel audit={professionalAudit} symbol={data.symbol} />
      </RecommendationDetailDisclosure>

      {data.fund_instrument_analysis ? (
        <RecommendationDetailDisclosure
          badge={`${data.fund_instrument_analysis.holding_count.toLocaleString("ko-KR")}개 보유`}
          eyebrow="ETF·펀드 심층 근거"
          id="recommendation-fund-analysis"
          summary="ETF는 기업 실적보다 구성종목, 비용률, NAV 괴리, 유동성, 추적 품질로 판단한다."
          title={`${data.symbol} 보유 구성과 추적 품질`}
          tone={data.fund_instrument_analysis.holding_count > 0 ? "ready" : "watch"}
        >
          <RecommendationFundInstrumentAnalysisPanel analysis={data.fund_instrument_analysis} />
        </RecommendationDetailDisclosure>
      ) : (
        <>
          <RecommendationDetailDisclosure
            badge={`${financialStatementModel.computed_metric_count}개 지표`}
            eyebrow="기업 재무 심층 근거"
            id="recommendation-financial-model"
            summary="재무 품질, 현금흐름, 부채, 희석, 산업 내 위치를 추천 근거와 분리해 대조한다."
            title={`${data.symbol} 재무·산업 근거`}
            tone={financialStatementModel.status === "available" || financialStatementModel.status === "partial" ? "ready" : "watch"}
          >
            <RecommendationFinancialStatementModelPanel model={financialStatementModel} symbol={data.symbol} />
            <RecommendationIndustryCompetitivePositionPanel
              peerComponent={peerComponent}
              position={data.industry_competitive_position}
              symbol={data.symbol}
            />
          </RecommendationDetailDisclosure>

          <RecommendationDetailDisclosure
            badge={valuationTargetRange.status === "available" ? `${valuationTargetRange.method_count}개 방법` : "가격 근거 대기"}
            eyebrow="밸류에이션 심층 근거"
            id="recommendation-valuation"
            summary="목표가 범위, 상승여지, 안전마진을 뉴스와 사이클 신호와 분리해 대조한다."
            title={`${data.symbol} 가치 범위`}
            tone={valuationTargetRange.status === "available" ? "ready" : "watch"}
          >
            <ValuationTargetRangeCard
              valuation={displayValuationTargetRange}
              eyebrow="가격·밸류에이션 근거"
              title={`${data.symbol} 목표가 범위와 상승여지`}
            />
          </RecommendationDetailDisclosure>

          <RecommendationDetailDisclosure
            badge={equityResearch ? `${equityResearch.key_points.length}개 포인트` : "리서치 대기"}
            eyebrow="기업 리서치"
            id="recommendation-equity-research"
            summary="사업 설명, 촉매, 리스크, 무효화 조건은 추천 채택 전에 별도로 펼쳐 원문과 대조한다."
            title={`${data.symbol} 기업 리서치 연결`}
            tone={equityResearch ? "ready" : "watch"}
          >
            <RecommendationEquityResearchPanel
              equityResearch={equityResearch}
              symbol={data.symbol}
              valuationItems={valuationItems}
            />
          </RecommendationDetailDisclosure>
        </>
      )}

      <RecommendationScoreComponentPanels
        symbol={data.symbol}
        isCompany={isCompany}
        cycleStack={scoreStacks.cycleStack}
        fundamentalStack={scoreStacks.fundamentalStack}
        brokerStack={scoreStacks.brokerStack}
      />

      <RecommendationDetailDisclosure
        badge={`${traceCards.length}개 연결`}
        eyebrow="뉴스·시장 근거"
        id="recommendation-evidence-review"
        summary="뉴스, 상위 흐름, validator 결과, 점수 출처를 한곳에 묶되 기본 판단 흐름에서는 접어둔다."
        title="이 추천에 붙은 근거를 원천까지 대조한다"
        tone={blockedEvidenceCount > 0 ? "blocked" : qualityDecision.tone === "risk-high" ? "blocked" : "watch"}
      >
        <RecommendationEvidenceTracePanel cards={traceCards} />
        <RecommendationMacroFlowPanel symbol={data.symbol} components={scoreStacks.macroFlowComponents} />
        <RecommendationEvidenceReviewPanel evidenceReview={data.evidence_review} />
        <RecommendationScoreAuditPanel data={data} />
      </RecommendationDetailDisclosure>
    </>
  );
}
