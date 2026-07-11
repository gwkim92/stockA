import type {
  RecommendationProductProfile,
  RecommendationQualityDecision,
} from "@/components/recommendation-product-overview";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import type { RecommendationWaterfallCard } from "./RecommendationDecisionFlowPanels";
import {
  formatPanelCurrency,
  formatPanelExpenseRatio,
  fundPanelStatusLabel,
  recommendationPanelOrderBoundaryLabel,
} from "./recommendation-panel-format";
import { isZeroWeight, type ScoreComponent } from "./recommendation-score-component-model";

type ProfessionalEvidenceAudit = RecommendationDetailData["professional_evidence_audit"];

type WaterfallModelInput = {
  readonly data: RecommendationDetailData;
  readonly productProfile: RecommendationProductProfile;
  readonly cycleStack: readonly ScoreComponent[];
  readonly macroFlowComponents: readonly ScoreComponent[];
  readonly qualityDecision: RecommendationQualityDecision;
  readonly decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  readonly professionalAudit: ProfessionalEvidenceAudit;
  readonly outcomeMeasured: boolean;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatOptionalPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return formatPercent(value);
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
}

function fundProductWaterfallCards(
  data: RecommendationDetailData,
  fundAnalysis: NonNullable<RecommendationDetailData["fund_instrument_analysis"]>,
): readonly RecommendationWaterfallCard[] {
  return [
    {
      step: "03",
      label: "ETF 구성",
      title: `${fundAnalysis.holding_count.toLocaleString("ko-KR")}개 보유종목`,
      body: `벤치마크 ${fundAnalysis.benchmark_code || data.symbol} 기준 보유 구성 커버리지 ${formatOptionalPercent(fundAnalysis.holdings_coverage_weight)}가 연결됐다.`,
      href: "#recommendation-fund-analysis",
      hrefLabel: "ETF 구성 보기",
      tone: fundAnalysis.holding_count > 0 ? "ready" : "watch",
    },
    {
      step: "04",
      label: "비용·추적",
      title: `${formatPanelExpenseRatio(fundAnalysis.expense_ratio.value)} · ${
        fundAnalysis.tracking_error.metric_type === "tracking_difference"
          ? formatOptionalPercent(fundAnalysis.tracking_error.tracking_difference_value)
          : koCode(fundAnalysis.tracking_error.status)
      }`,
      body: "ETF는 기업 DCF가 아니라 비용률, 벤치마크 추적 차이, NAV 기준 괴리로 보유 품질이 갈린다.",
      href: "#recommendation-fund-analysis",
      hrefLabel: "비용·추적 보기",
      tone: "ready",
    },
    {
      step: "05",
      label: "NAV·유동성",
      title: `${formatOptionalPercent(fundAnalysis.nav_premium_discount.premium_discount_to_nav)} · ${fundPanelStatusLabel(fundAnalysis.liquidity.status)}`,
      body: `NAV 괴리와 거래대금은 실제 편입·리밸런싱 부담을 보여준다. 평균 거래대금 ${formatPanelCurrency(fundAnalysis.liquidity.average_daily_dollar_volume, data.currency_code)}.`,
      href: "#recommendation-fund-analysis",
      hrefLabel: "NAV·유동성 보기",
      tone: "ready",
    },
  ];
}

function companyProductWaterfallCards({
  data,
  professionalAudit,
  sourceBlocked,
  valuationReady,
}: {
  readonly data: RecommendationDetailData;
  readonly professionalAudit: ProfessionalEvidenceAudit;
  readonly sourceBlocked: boolean;
  readonly valuationReady: boolean;
}): readonly RecommendationWaterfallCard[] {
  return [
    {
      step: "03",
      label: "기업",
      title: data.equity_research ? "리서치 연결" : "리서치 대기",
      body: data.equity_research
        ? "사업 설명, 촉매, 리스크, 무효화 조건이 기업 리서치로 연결됐다."
        : "기업 리서치 결과가 아직 없어 사업 맥락 확인이 제한된다.",
      href: "#recommendation-equity-research",
      hrefLabel: "기업 리서치 보기",
      tone: data.equity_research ? "ready" : "watch",
    },
    {
      step: "04",
      label: "재무",
      title:
        data.financial_statement_model.status === "available" || data.financial_statement_model.status === "partial"
          ? `${data.financial_statement_model.computed_metric_count}개 지표`
          : "재무 원천 부족",
      body: sourceBlocked
        ? koLabel(professionalAudit.source_blocker.summary)
        : `재무 품질·현금흐름·부채·희석 지표 ${data.financial_statement_model.computed_metric_count}개가 연결됐다.`,
      href: "#recommendation-financial-model",
      hrefLabel: "재무 근거 보기",
      tone: sourceBlocked
        ? "blocked"
        : data.financial_statement_model.status === "available" || data.financial_statement_model.status === "partial"
          ? "ready"
          : "watch",
    },
    {
      step: "05",
      label: "밸류에이션",
      title: valuationReady ? `${data.valuation_target_range.method_count}개 방법` : "가격 근거 대기",
      body: valuationReady
        ? `기준 상승여지 ${formatOptionalPercent(data.valuation_target_range.upside_base)}와 안전마진 ${formatOptionalPercent(data.valuation_target_range.margin_of_safety)}를 반영한 가치 범위입니다.`
        : "목표가 범위나 안전마진이 충분히 연결되지 않았다.",
      href: "#recommendation-valuation",
      hrefLabel: "밸류에이션 보기",
      tone: valuationReady ? "ready" : "watch",
    },
  ];
}

export function recommendationWaterfallCards({
  data,
  productProfile,
  cycleStack,
  macroFlowComponents,
  qualityDecision,
  decisionWaterfall,
  professionalAudit,
  outcomeMeasured,
}: WaterfallModelInput): RecommendationWaterfallCard[] {
  const macroComponent = cycleStack.find((component) => component.component === "macro_regime_score");
  const themeComponent =
    cycleStack.find((component) => component.component === "theme_cycle_score") ?? macroFlowComponents[0];
  const valuationReady = data.valuation_target_range.status === "available";
  const sourceBlocked = professionalAudit.source_blocker.blocked || data.professional_decision_waterfall.status === "source_data_blocked";
  const riskBlocked = professionalAudit.blocked_layer_count > 0 || reviewCount(data.evidence_review.summary.blocked_count) > 0;
  const fundAnalysis = data.fund_instrument_analysis;
  const productCards =
    productProfile.kind === "fund_or_etf" && fundAnalysis
      ? fundProductWaterfallCards(data, fundAnalysis)
      : companyProductWaterfallCards({ data, professionalAudit, sourceBlocked, valuationReady });

  return [
    {
      step: "01",
      label: "거시",
      title: macroComponent ? formatPercent(macroComponent.value) : "거시 근거 대기",
      body: macroComponent
        ? `금리·물가·유동성 같은 상위 환경이 ${data.symbol} 분석 배경으로 연결됐다. ${isZeroWeight(macroComponent.weight) ? "현재 최종 점수 영향은 없다." : "최종 점수에 반영된다."}`
        : "거시 사이클 점수 항목이 아직 연결되지 않았다.",
      href: "#recommendation-cycle-stack",
      hrefLabel: "사이클 근거 보기",
      tone: macroComponent ? "ready" : "watch",
    },
    {
      step: "02",
      label: "테마",
      title: themeComponent ? formatPercent(themeComponent.value) : "테마 전파 대기",
      body: macroFlowComponents.length > 0
        ? `상위 흐름 전파 ${macroFlowComponents.length}개 점수 항목이 있다. 회사명이 직접 언급되지 않아도 노출도 규칙으로 연결된다.`
        : themeComponent
          ? "테마 사이클 항목은 있으나 최근 상위 흐름 전파 근거는 적다."
          : "테마·상위 흐름 전파 근거가 아직 추천 입력으로 연결되지 않았다.",
      href: "#recommendation-macro-flow",
      hrefLabel: "흐름 전파 보기",
      tone: themeComponent || macroFlowComponents.length > 0 ? "ready" : "watch",
    },
    ...productCards,
    {
      step: "06",
      label: "리스크",
      title: qualityDecision.status,
      body: riskBlocked
        ? "차단된 근거나 전문 분석 원천 문제가 있어 추천은 기록으로만 남긴다."
        : outcomeMeasured
          ? `성과 측정 완료. 알파 ${formatPercent(data.outcome.alpha)}와 근거 검증 기준이 연결됐다.`
          : "성과 측정창이 아직 끝나지 않았다. 추천 산식 변경이나 자동 주문은 금지 상태다.",
      href: "#recommendation-evidence-review",
      hrefLabel: "리스크 점검 보기",
      tone: riskBlocked ? "blocked" : qualityDecision.tone === "risk-low" ? "ready" : "watch",
    },
    {
      step: "07",
      label: "가상 매매 검증",
      title: decisionWaterfall.paper_validation_input_allowed ? "입력 가능" : "입력 차단",
      body: decisionWaterfall.paper_validation_input_allowed
        ? `가상 매매 검증 입력은 가능하지만 실거래 상태는 ${recommendationPanelOrderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`
        : `가상 매매 검증 입력 전 차단 조건이 남아 있다. 실거래 상태는 ${recommendationPanelOrderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`,
      href: "/paper-trading",
      hrefLabel: "가상 매매 상태",
      tone: decisionWaterfall.paper_validation_input_allowed ? "watch" : "blocked",
    },
  ];
}
