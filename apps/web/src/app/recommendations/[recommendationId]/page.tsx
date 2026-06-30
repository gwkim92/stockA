import type { Route } from "next";
import { RecommendationExecutiveBrief } from "@/components/recommendation-executive-brief";
import { RecommendationPositionReality } from "@/components/recommendation-position-reality";
import {
  type RecommendationProductProfile,
  type RecommendationQualityDecision,
} from "@/components/recommendation-product-overview";
import { getRecommendationDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import { buildRecommendationViewModel, recommendationCopy, recommendationProductKind } from "@/lib/presentation";
import type { RecommendationDetailData } from "@/lib/types";

import { RecommendationCompatibilityReport } from "./_components/RecommendationCompatibilityReport";
import { RecommendationDecisionHeader } from "./_components/RecommendationDecisionHeader";
import {
  RecommendationDecisionWaterfall,
  type RecommendationFocusItem,
  type RecommendationWaterfallCard,
} from "./_components/RecommendationDecisionFlowPanels";
import { type RecommendationEvidenceTraceCard } from "./_components/RecommendationEvidenceTracePanel";
import { RecommendationMarketCorrelationsPanel } from "./_components/RecommendationMarketCorrelationsPanel";
import { RecommendationProfessionalDetailSections } from "./_components/RecommendationProfessionalDetailSections";
import { RecommendationQualityBoundaryPanel } from "./_components/RecommendationQualityBoundaryPanel";
import {
  brokerComponents,
  cycleStackComponents,
  fundamentalComponents,
  isZeroWeight,
  macroFlowRows,
  type ScoreComponent,
} from "./_components/recommendation-score-component-model";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천 상세" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

type ProfessionalEvidenceAudit = RecommendationDetailData["professional_evidence_audit"];

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

function formatOptionalPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return formatPercent(value);
}

function formatCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "데이터 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 0,
  }).format(value);
}

function formatExpenseRatio(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "비용률 자료 없음";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  })}%`;
}

function fundStatusLabel(status: string) {
  if (status === "collected" || status === "available") {
    return "수집 완료";
  }
  if (status === "missing") {
    return "데이터 없음";
  }
  if (status === "stale") {
    return "오래된 자료";
  }
  return koCode(status);
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

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
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

function recommendationQualityDecision(data: RecommendationDetailData): RecommendationQualityDecision {
  const blockedCount = reviewCount(data.evidence_review.summary.blocked_count);
  const warningCount = reviewCount(data.evidence_review.summary.warning_count);
  const sourceDataBlocked = data.professional_decision_waterfall.status === "source_data_blocked";
  const adverseRecommendation = ["avoid", "exclude", "sell", "exit"].includes(data.recommendation);
  const weakScore = data.score < 0.35;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const negativeAlpha = outcomeMeasured && data.outcome.alpha < 0;

  if (sourceDataBlocked) {
    return {
      status: "전문 재무 원천 차단",
      tone: "risk-high",
      summary: "정기 재무제표나 검증된 해석기가 없어 이 추천은 기록으로만 보존한다. 뉴스·가격 근거가 있어도 전문 분석이나 가상 매매 검증 입력으로 넘기면 안 된다.",
    };
  }
  if (blockedCount > 0) {
    return {
      status: "분석 입력 차단",
      tone: "risk-high",
      summary: "연결된 투자 논리, 점수 구성요소, 성과 측정 중 차단 조건이 있어 투자 분석 입력으로 넘기면 안 된다.",
    };
  }
  if (adverseRecommendation || weakScore) {
    return {
      status: "투자 보류",
      tone: "risk-high",
      summary: "현재 추천 조치나 점수가 중장기 신규 투자 신호로 보기 어렵다. 근거는 보존하되 채택하지 않는다.",
    };
  }
  if (warningCount > 0 || negativeAlpha || !outcomeMeasured) {
    return {
      status: "근거 보강 대기",
      tone: "risk-medium",
      summary: "핵심 근거는 있으나 성과 측정, 근거 연결, 또는 최근 성과가 충분히 강하지 않아 근거 보강이 먼저다.",
    };
  }
  return {
    status: "투자 근거 품질 통과",
    tone: "risk-low",
    summary: "근거와 성과가 연결되어 있어 중장기 투자 신호 품질 기준을 통과했다.",
  };
}

function recommendationQualityChecks(data: RecommendationDetailData) {
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const aiEvidenceCount = reviewCount(data.evidence_review.summary.ai_evidence_component_count);
  const marketProvenanceCount = reviewCount(data.evidence_review.summary.market_or_rank_provenance_count);
  return [
    {
      label: "점수 강도",
      value: data.score >= 0.65 ? "강함" : data.score >= 0.35 ? "관찰 가능" : "약함",
      detail: `현재 점수 ${formatPercent(data.score)} · 추천 조치 ${koCode(data.recommendation)}`,
    },
    {
      label: "근거 연결",
      value: ["ai_review_passed", "ready_for_human_review"].includes(data.evidence_review.quality_status)
        ? "품질 기준 통과"
        : koCode(data.evidence_review.quality_status),
      detail: `뉴스·투자 근거 ${aiEvidenceCount}개 · 가격/순위 출처 기록 ${marketProvenanceCount}개`,
    },
    {
      label: "성과 확인",
      value: outcomeMeasured ? koCode(data.outcome.label) : "성과 미측정",
      detail: outcomeMeasured
        ? `알파 ${formatPercent(data.outcome.alpha)} · 측정 종료 ${data.outcome.measurement_end_date}`
        : "성과 측정 기간이 끝나면 성과 기록을 생성해야 한다.",
    },
    {
      label: "실거래 상태",
      value: "자동 주문 없음",
      detail: "이 결과는 추천 품질 상태이며 증권사 주문 연결을 실행하지 않는다.",
    },
  ];
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

function qualityToneToFocusTone(tone: RecommendationQualityDecision["tone"]): RecommendationFocusItem["tone"] {
  if (tone === "risk-high") {
    return "blocked";
  }
  if (tone === "risk-medium") {
    return "watch";
  }
  return "ready";
}

function recommendationImmediateFocus({
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
}: {
  data: RecommendationDetailData;
  productProfile: RecommendationProductProfile;
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  professionalAudit: ProfessionalEvidenceAudit;
  blockedDecisionStepCount: number;
  watchDecisionStepCount: number;
  outcomeMeasured: boolean;
  marketCorrelationCount: number;
  macroFlowComponents: ScoreComponent[];
  fundamentalStack: ScoreComponent[];
}): RecommendationFocusItem[] {
  const items: RecommendationFocusItem[] = [];
  const aiEvidenceCount = reviewCount(data.evidence_review.summary.ai_evidence_component_count);
  const directEvidenceStatus = data.evidence_trace.direct_news_or_ai.status;
  const financialMetricCount = data.financial_statement_model.computed_metric_count;
  const sourceBlocked = professionalAudit.source_blocker.blocked || decisionWaterfall.status === "source_data_blocked";
  const fundAnalysis = data.fund_instrument_analysis;

  if (sourceBlocked) {
    items.push({
      label: "1순위",
      title: "원천 근거 차단부터 확인",
      body: "정기 재무제표나 검증 가능한 원천이 부족하면 뉴스 근거가 있어도 전문 판단이나 가상 매매 입력으로 넘기지 않는다.",
      metric: "전문 판단 입력 금지",
      href: "#recommendation-evidence-review",
      hrefLabel: "차단 근거 보기",
      tone: "blocked",
    });
  } else if (blockedDecisionStepCount > 0) {
    items.push({
      label: "1순위",
      title: "막힌 분석 단계가 먼저다",
      body: "어느 단계가 막혔는지 알아야 뒤의 재무·밸류·뉴스 근거를 투자 판단에 쓸 수 있다.",
      metric: `차단 ${blockedDecisionStepCount.toLocaleString("ko-KR")}개`,
      href: "#recommendation-professional-flow",
      hrefLabel: "전문 분석 흐름 보기",
      tone: "blocked",
    });
  } else if (!decisionWaterfall.paper_validation_input_allowed) {
    items.push({
      label: "1순위",
      title: "가상 매매 입력이 막혀 있다",
      body: "전문 분석 일부는 통과했더라도 가상 매매 검증으로 넘길 조건이 아직 부족하다.",
      metric: "가상 매매 입력 차단",
      href: "/paper-trading",
      hrefLabel: "가상 매매 상태 보기",
      tone: "blocked",
    });
  } else if (!outcomeMeasured) {
    items.push({
      label: "1순위",
      title: "성과 측정창 종료 대기",
      body: "추천 근거는 연결됐지만 성과 측정창이 끝나지 않았다. 이 기간에는 추천 산식 변경과 실거래 주문을 하지 않는다.",
      metric: "성과 미측정",
      href: "#recommendation-evidence-review",
      hrefLabel: "성과·리스크 보기",
      tone: "watch",
    });
  } else {
    items.push({
      label: "1순위",
      title: "최종 결론과 반대 신호",
      body: qualityDecision.summary,
      metric: qualityDecision.status,
      href: "#recommendation-professional-flow",
      hrefLabel: "전문 분석 흐름 보기",
      tone: qualityToneToFocusTone(qualityDecision.tone),
    });
  }

  items.push({
    label: "근거",
    title: "뉴스·상위 흐름 근거 보기",
    body:
      directEvidenceStatus === "linked"
        ? "직접 종목 뉴스가 추천 근거로 연결됐다. 원천 뉴스, 한국어 요약, 종목 영향 방향을 한 줄로 추적한다."
        : "직접 종목 뉴스보다 상위 흐름, 가격, 종목군 순위 근거가 중심이다. 연결 경로를 추적한다.",
    metric: `뉴스 근거 ${aiEvidenceCount.toLocaleString("ko-KR")}개 · 흐름 ${macroFlowComponents.length.toLocaleString("ko-KR")}개`,
    href: "#recommendation-evidence-trace",
    hrefLabel: "근거 경로 보기",
    tone: aiEvidenceCount > 0 || macroFlowComponents.length > 0 ? "ready" : "watch",
  });

  if (productProfile.kind === "fund_or_etf" && fundAnalysis) {
    items.push({
      label: "ETF",
      title: "보유종목·비용·추적 품질",
      body: "ETF 추천은 기업 실적표보다 보유종목 구성, 벤치마크 추적, 비용률, NAV 괴리와 유동성이 핵심이다.",
      metric: `${fundAnalysis.holding_count.toLocaleString("ko-KR")}개 보유 · 비용률 ${formatExpenseRatio(fundAnalysis.expense_ratio.value)}`,
      href: "#recommendation-fund-analysis",
      hrefLabel: "ETF 근거 보기",
      tone: fundAnalysis.status === "available" || fundAnalysis.holding_count > 0 ? "ready" : "watch",
    });
  } else {
    items.push({
      label: "기업",
      title: "재무·밸류에이션 근거",
      body: "개별 회사 추천은 뉴스만으로 판단하지 않는다. 재무 품질, 밸류에이션, 피어 비교의 공백과 차단 여부를 분리한다.",
      metric: `재무 ${financialMetricCount.toLocaleString("ko-KR")}개 · 재무항목 ${fundamentalStack.length.toLocaleString("ko-KR")}개`,
      href: financialMetricCount > 0 ? "#recommendation-financial-model" : "#recommendation-valuation",
      hrefLabel: financialMetricCount > 0 ? "재무 모델 보기" : "밸류에이션 보기",
      tone: financialMetricCount > 0 || fundamentalStack.length > 0 ? "ready" : "watch",
    });
  }

  items.push({
      label: "시장",
      title: "시장 동조성과 외부 지표",
      body: "지수·섹터·금리·달러·원자재와의 동조성을 함께 두면 종목 단독 착시를 줄일 수 있다.",
    metric: `비교 ${marketCorrelationCount.toLocaleString("ko-KR")}개`,
    href: "#recommendation-market-correlations",
    hrefLabel: "시장 동조성 보기",
    tone: marketCorrelationCount > 0 ? "ready" : "watch",
  });

  if (watchDecisionStepCount > 0 && items.length < 5) {
    items.push({
      label: "주의",
      title: "주의 단계가 남아 있다",
      body: "차단은 아니지만 주의 단계가 남아 있다. 남은 항목이 해소되기 전까지 추천 채택을 보류한다.",
      metric: `주의 ${watchDecisionStepCount.toLocaleString("ko-KR")}개`,
      href: "#recommendation-professional-flow",
      hrefLabel: "주의 단계 보기",
      tone: "watch",
    });
  }

  return items.slice(0, 4);
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

function recommendationWaterfallCards({
  data,
  productProfile,
  cycleStack,
  macroFlowComponents,
  fundamentalStack,
  qualityDecision,
  decisionWaterfall,
  professionalAudit,
  outcomeMeasured,
}: {
  data: RecommendationDetailData;
  productProfile: RecommendationProductProfile;
  cycleStack: ScoreComponent[];
  macroFlowComponents: ScoreComponent[];
  fundamentalStack: ScoreComponent[];
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  professionalAudit: ProfessionalEvidenceAudit;
  outcomeMeasured: boolean;
}): RecommendationWaterfallCard[] {
  const macroComponent = cycleStack.find((component) => component.component === "macro_regime_score");
  const themeComponent =
    cycleStack.find((component) => component.component === "theme_cycle_score") ?? macroFlowComponents[0];
  const valuationReady = data.valuation_target_range.status === "available";
  const sourceBlocked = professionalAudit.source_blocker.blocked || data.professional_decision_waterfall.status === "source_data_blocked";
  const riskBlocked = professionalAudit.blocked_layer_count > 0 || reviewCount(data.evidence_review.summary.blocked_count) > 0;
  const fundAnalysis = data.fund_instrument_analysis;
  const productCards: RecommendationWaterfallCard[] =
    productProfile.kind === "fund_or_etf" && fundAnalysis
      ? [
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
            title: `${formatExpenseRatio(fundAnalysis.expense_ratio.value)} · ${
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
            title: `${formatOptionalPercent(fundAnalysis.nav_premium_discount.premium_discount_to_nav)} · ${fundStatusLabel(fundAnalysis.liquidity.status)}`,
            body: `NAV 괴리와 거래대금은 실제 편입·리밸런싱 부담을 보여준다. 평균 거래대금 ${formatCurrency(fundAnalysis.liquidity.average_daily_dollar_volume, data.currency_code)}.`,
            href: "#recommendation-fund-analysis",
            hrefLabel: "NAV·유동성 보기",
            tone: "ready",
          },
        ]
      : [
          {
            step: "03",
            label: "기업",
            title: data.equity_research ? "리서치 연결" : "리서치 대기",
            body: data.equity_research
              ? "사업 설명, 촉매, 리스크, 무효화 조건이 기업 리서치로 연결됐다."
              : "기업 리서치 결과가 아직 없어 사업 맥락은 제한적으로만 볼 수 있다.",
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
        ? `가상 매매 검증 입력은 가능하지만 실거래 상태는 ${orderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`
        : `가상 매매 검증 입력 전 차단 조건이 남아 있다. 실거래 상태는 ${orderBoundaryLabel(decisionWaterfall.order_boundary)}이다.`,
      href: "/paper-trading",
      hrefLabel: "가상 매매 상태",
      tone: decisionWaterfall.paper_validation_input_allowed ? "watch" : "blocked",
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
    fundamentalStack,
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
