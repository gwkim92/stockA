import { memoEvidenceAssessment } from "@/lib/recommendation-memo-model";
import type {
  RecommendationProductProfile,
  RecommendationQualityDecision,
} from "@/components/recommendation-product-overview";
import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

import type { RecommendationFocusItem } from "./RecommendationDecisionFlowPanels";
import { formatPanelExpenseRatio } from "./recommendation-panel-format";
import type { ScoreComponent } from "./recommendation-score-component-model";

type ProfessionalEvidenceAudit = RecommendationDetailData["professional_evidence_audit"];

export type RecommendationQualityCheck = {
  readonly label: string;
  readonly value: string;
  readonly detail: string;
};

type ImmediateFocusModelInput = {
  readonly data: RecommendationDetailData;
  readonly productProfile: RecommendationProductProfile;
  readonly qualityDecision: RecommendationQualityDecision;
  readonly decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
  readonly professionalAudit: ProfessionalEvidenceAudit;
  readonly blockedDecisionStepCount: number;
  readonly watchDecisionStepCount: number;
  readonly outcomeMeasured: boolean;
  readonly marketCorrelationCount: number;
  readonly macroFlowComponents: readonly ScoreComponent[];
  readonly fundamentalStack: readonly ScoreComponent[];
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
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

export function recommendationQualityDecision(data: RecommendationDetailData): RecommendationQualityDecision {
  const blockedCount = reviewCount(data.evidence_review.summary.blocked_count);
  const warningCount = reviewCount(data.evidence_review.summary.warning_count);
  const sourceDataBlocked = data.professional_decision_waterfall.status === "source_data_blocked" || data.professional_evidence_audit.source_blocker.blocked === true || data.professional_source_guardrail?.blocked === true;
  const adverseRecommendation = ["avoid", "exclude", "sell", "exit"].includes(data.recommendation);
  const weakScore = data.score < 0.35;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const negativeAlpha = outcomeMeasured && data.outcome.alpha < 0;

  if (sourceDataBlocked) {
    return {
      status: "전문 재무 원천 차단",
      tone: "risk-high",
      summary: "정기 재무제표나 검증된 해석기가 없어 이 추천은 기록으로만 보존한다. 뉴스·가격 근거가 있어도 전문 판단 입력이나 가상 매매 검증 입력으로 넘기면 안 된다.",
    };
  }
  if (memoEvidenceAssessment(data.professional_evidence_audit).label === "근거 상태 미확인") {
    return { status: "근거 상태 미확인", tone: "risk-medium", summary: "기대 근거 수와 감사 상태가 확인되지 않아 품질 통과로 간주하지 않습니다." };
  }
  if (blockedCount > 0) {
    return {
      status: "전문 판단 입력 차단",
      tone: "risk-high",
      summary: "연결된 투자 논리, 점수 구성요소, 성과 측정 중 차단 조건이 있어 전문 판단 입력으로 넘기면 안 된다.",
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

export function recommendationQualityChecks(data: RecommendationDetailData): readonly RecommendationQualityCheck[] {
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

export function recommendationImmediateFocus({
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
}: ImmediateFocusModelInput): RecommendationFocusItem[] {
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
      metric: `${fundAnalysis.holding_count.toLocaleString("ko-KR")}개 보유 · 비용률 ${formatPanelExpenseRatio(fundAnalysis.expense_ratio.value)}`,
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
    body: "지수·섹터·금리·달러·원자재와 함께 비교하면 종목 단독 착시가 줄어든다.",
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
