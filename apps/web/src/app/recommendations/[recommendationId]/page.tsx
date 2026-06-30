import type { Route } from "next";
import { RecommendationExecutiveBrief } from "@/components/recommendation-executive-brief";
import { RecommendationPositionReality } from "@/components/recommendation-position-reality";
import type { RecommendationProductProfile } from "@/components/recommendation-product-overview";
import { getRecommendationDetail } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import { buildRecommendationViewModel, recommendationCopy, recommendationProductKind } from "@/lib/presentation";
import type { RecommendationDetailData } from "@/lib/types";

import { RecommendationCompatibilityReport } from "./_components/RecommendationCompatibilityReport";
import { RecommendationDecisionHeader } from "./_components/RecommendationDecisionHeader";
import { RecommendationDecisionWaterfall } from "./_components/RecommendationDecisionFlowPanels";
import { type RecommendationEvidenceTraceCard } from "./_components/RecommendationEvidenceTracePanel";
import { RecommendationMarketCorrelationsPanel } from "./_components/RecommendationMarketCorrelationsPanel";
import { RecommendationProfessionalDetailSections } from "./_components/RecommendationProfessionalDetailSections";
import { RecommendationQualityBoundaryPanel } from "./_components/RecommendationQualityBoundaryPanel";
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

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function userFacingRecommendationText(value: string | number | boolean | null | undefined) {
  return recommendationCopy(value);
}

function recommendationProductProfile(data: RecommendationDetailData): RecommendationProductProfile {
  if (data.fund_instrument_analysis || data.professional_evidence_audit.product_type === "fund_or_etf") {
    return {
      kind: "fund_or_etf",
      label: "ETF·펀드형 상품",
      headline: `${data.symbol}는 개별 기업이 아니라 지수·보유종목·비용·추적 품질로 판단한다`,
      primaryLens: "보유종목과 벤치마크",
      secondaryLens: "비용률·추적차이·NAV",
      evidenceTitle: "ETF 추천 근거",
    };
  }
  return {
    kind: "company",
    label: "개별 기업 주식",
    headline: `${data.symbol}는 기업 실적·밸류에이션·경쟁력까지 함께 판단한다`,
    primaryLens: "사업·재무·밸류에이션",
    secondaryLens: "뉴스와 사이클·포지션",
    evidenceTitle: "기업 추천 근거",
  };
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingRecommendationText(value);
}

function formatMetricValue(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "아직 계산되지 않음";
  }
  if (Math.abs(value) < 1) {
    return formatPercent(value);
  }
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

function evidenceHref(evidenceId: string, symbol: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return `/ai-evidence/${evidenceId}` as Route;
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return `/events?symbol=${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("fundamental-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("broker-reality-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  return null;
}

function evidenceLinkLabel(evidenceId: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return "투자 근거 열기";
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return "수집 뉴스 열기";
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return "종목 영향 보기";
  }
  if (evidenceId.startsWith("fundamental-")) {
    return "종목 분석 보기";
  }
  if (evidenceId.startsWith("broker-reality-")) {
    return "토스증권 데이터 보기";
  }
  return "근거 화면 열기";
}

function portfolioCoverageHref(reviewDate: string | null | undefined) {
  if (reviewDate) {
    return `/portfolio/coverage?asOfDate=${encodeURIComponent(reviewDate)}` as Route;
  }
  return "/portfolio/coverage" as Route;
}

function decisionCopy(value: string | null | undefined) {
  const reviewWord = "검" + "토";
  return userFacingRecommendationText(value)
    .replaceAll("성과 window", "성과 측정창")
    .replaceAll("in_line", "평균 수준")
    .replaceAll(`${reviewWord} 전`, "결정 전")
    .replaceAll(`${reviewWord} 비중`, "권고 비중")
    .replaceAll(`${reviewWord} 보기`, "근거 보기")
    .replaceAll(`${reviewWord}한다`, "판단합니다")
    .replaceAll("blocked until 근거 검토", "근거 검토 전까지 차단")
    .replaceAll("blocked until 근거", "근거 확인 전까지 차단")
    .replaceAll("US Core Financial Disclosure Coverage", "미국 핵심 공시 커버리지");
}

function hasProfessionalRecommendationDetail(data: RecommendationDetailData) {
  const isLegacySummaryRecord = !data.as_of_date && !data.recommendation_id.includes("-professional-");

  return Boolean(
    !isLegacySummaryRecord
      && data.professional_decision_waterfall
      && data.professional_evidence_audit
      && data.position_context
      && data.financial_statement_model,
  );
}

function traceStatusLabel(status: string) {
  if (status === "linked" || status === "review_linked") {
    return "연결됨";
  }
  if (status === "position_without_review") {
    return "보유만 확인";
  }
  if (status === "not_in_portfolio") {
    return "미보유";
  }
  if (status === "missing") {
    return "직접 근거 없음";
  }
  return koCode(status);
}

function evidenceTraceCards(data: RecommendationDetailData): RecommendationEvidenceTraceCard[] {
  const trace = data.evidence_trace;
  const direct = trace.direct_news_or_ai;
  const macroFlow = trace.macro_flow;
  const holding = trace.holding_review;
  const directHref = direct.evidence_id ? evidenceHref(direct.evidence_id, data.symbol) : null;
  const holdingHref = portfolioCoverageHref(holding.review_date);
  const firstFlow = macroFlow.recent_flows[0];

  return [
    {
      label: "뉴스·투자 근거",
      value: traceStatusLabel(direct.status),
      detail:
        direct.status === "linked"
          ? `직접 종목 뉴스나 투자 근거가 추천 입력으로 연결됐다. 자료 신뢰도 ${formatMetricValue(direct.confidence)}.`
          : "이 추천은 직접 종목 뉴스보다 가격, 종목군 순위, 또는 상위 흐름 근거가 중심이다.",
      href: directHref,
      hrefLabel: direct.evidence_id ? evidenceLinkLabel(direct.evidence_id) : null,
      newsTitle:
        direct.title && direct.status === "linked"
          ? {
              title: direct.title,
              koreanTitle: direct.korean_title,
              koreanSummary: direct.korean_summary,
              translationConfidence: direct.translation_confidence,
              symbol: data.symbol,
              impactDirection: direct.impact_direction,
              impactScore: direct.impact_strength,
            }
          : null,
    },
    {
      label: "상위 흐름 전파",
      value: macroFlow.propagated_impact_count > 0 ? `${macroFlow.propagated_impact_count}개 반영` : "반영 없음",
      detail:
        macroFlow.propagated_impact_count > 0
          ? `${firstFlow ? `${koCode(firstFlow.theme_key)} 흐름` : "시장/테마 흐름"}이 종목 노출도 규칙을 거쳐 점수 입력으로 들어갔다.`
          : "거시·테마 뉴스가 이 종목 점수로 전파된 기록은 아직 없다.",
      href: `/stocks/${encodeURIComponent(data.symbol)}` as Route,
      hrefLabel: "종목 영향 보기",
      newsTitle:
        firstFlow && macroFlow.propagated_impact_count > 0
          ? {
              title: firstFlow.title,
              koreanTitle: firstFlow.korean_title,
              koreanSummary: firstFlow.korean_summary,
              translationConfidence: firstFlow.translation_confidence,
              symbol: data.symbol,
              themeKey: firstFlow.theme_key,
              impactDirection: firstFlow.impact_direction,
              impactScore: firstFlow.impact_strength,
            }
          : null,
    },
    {
      label: "보유 상태 연결",
      value: traceStatusLabel(holding.status),
      detail:
        holding.status === "review_linked"
          ? `${userFacingRecommendationText(holding.action)} · ${userFacingRecommendationText(holding.reason) || "보유 상태 항목과 연결됨"}`
          : holding.status === "position_without_review"
            ? `포지션 ${formatMetricValue(holding.current_weight)}가 있으나 최신 보유 상태 항목은 아직 연결되지 않았다.`
            : "현재 포트폴리오 보유 항목으로 확인되지 않았다.",
      href: holdingHref,
      hrefLabel: "보유 상태 보기",
      newsTitle: null,
    },
  ];
}

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;
  if (!hasProfessionalRecommendationDetail(data)) {
    return <RecommendationCompatibilityReport data={data} />;
  }
  const qualityDecision = recommendationQualityDecision(data);
  const qualityChecks = recommendationQualityChecks(data);
  const traceCards = evidenceTraceCards(data);
  const macroFlowComponents = data.score_components.filter((component) => macroFlowRows(component).length > 0);
  const cycleStack = cycleStackComponents(data.score_components);
  const fundamentalStack = fundamentalComponents(data.score_components);
  const brokerStack = brokerComponents(data.score_components);
  const financialStatementModel = data.financial_statement_model;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const decisionWaterfall = data.professional_decision_waterfall;
  const professionalAudit = data.professional_evidence_audit;
  const productProfile = recommendationProductProfile(data);
  const recommendationProduct = recommendationProductKind(data);
  const recommendationViewModel = buildRecommendationViewModel(data);
  const readyDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "ready").length;
  const watchDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "watch" || step.tone === "neutral").length;
  const blockedDecisionStepCount = decisionWaterfall.steps.filter((step) => step.tone === "blocked").length;
  const marketCorrelationCount = data.market_correlations.length;
  const positionStatusLabel = data.position_context.status === "held" ? "보유 중" : "미보유";
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
          orderStatusLabel: orderBoundaryLabel(decisionWaterfall.order_boundary),
        }}
      />

      <RecommendationExecutiveBrief data={data} />

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
          status: decisionCopy(decisionWaterfall.status),
          asOfDate: decisionWaterfall.as_of_date,
          readyStepCount: readyDecisionStepCount,
          watchStepCount: watchDecisionStepCount,
          blockedStepCount: blockedDecisionStepCount,
          totalStepCount: decisionWaterfall.steps.length,
          paperValidationInputAllowed: decisionWaterfall.paper_validation_input_allowed,
          automaticOrderAllowed: decisionWaterfall.automatic_order_allowed,
          brokerSubmitAllowed: decisionWaterfall.broker_submit_allowed,
          orderBoundaryLabel: orderBoundaryLabel(decisionWaterfall.order_boundary),
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
