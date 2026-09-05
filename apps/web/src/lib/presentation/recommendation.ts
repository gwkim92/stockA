import type { RecommendationDetailData } from "../types";
import { memoPositionLabel, memoEvidenceAssessment } from "../recommendation-memo-model";

import { recommendationCopy } from "./investment-copy";
import { formatPercent } from "./format";
import type { InvestmentViewModel } from "./view-model";

export type RecommendationProductKind = "company_stock" | "fund_or_etf";

export function recommendationProductKind(data: Pick<RecommendationDetailData, "fund_instrument_analysis"> & Partial<Pick<RecommendationDetailData, "professional_evidence_audit">>): RecommendationProductKind {
  return data.fund_instrument_analysis || data.professional_evidence_audit?.product_type === "fund_or_etf" ? "fund_or_etf" : "company_stock";
}

export function recommendationProductLabel(kind: RecommendationProductKind): string {
  if (kind === "fund_or_etf") {
    return "ETF·펀드";
  }
  return "개별 회사 주식";
}

export function recommendationExecutionStatus(
  decision: Pick<RecommendationDetailData["professional_decision_waterfall"], "broker_submit_allowed" | "paper_validation_input_allowed">,
): Pick<InvestmentViewModel, "statusLabel" | "statusTone" | "nextAction"> {
  if (decision.broker_submit_allowed) {
    return {
      statusLabel: "실거래 가능",
      statusTone: "ready",
      nextAction: "실거래 전 계좌 권한, 주문 한도, 포지션 크기를 다시 대조합니다.",
    };
  }
  if (decision.paper_validation_input_allowed) {
    return {
      statusLabel: "가상 검증 가능",
      statusTone: "watch",
      nextAction: "실거래는 차단된 상태에서 가상 매매 검증 결과를 먼저 봅니다.",
    };
  }
  return {
    statusLabel: "실행 차단",
    statusTone: "blocked",
    nextAction: "차단 사유와 부족한 근거를 해소하기 전에는 주문 후보로 보지 않습니다.",
  };
}

export function buildRecommendationViewModel(data: RecommendationDetailData): InvestmentViewModel {
  const kind = recommendationProductKind(data);
  const execution = recommendationExecutionStatus(data.professional_decision_waterfall);
  const sourceBlocked =
    data.professional_evidence_audit.source_blocker.blocked
    || data.professional_source_guardrail?.blocked === true
    || data.professional_decision_waterfall.status === "source_data_blocked";
  const positionLabel = memoPositionLabel(data.position_context.status);
  const scoreLabel = formatPercent(data.score);

  return {
    title: `${data.symbol} ${recommendationProductLabel(kind)} 추천 판단서`,
    summary: `${recommendationCopy(data.recommendation)} · 점수 ${scoreLabel} · ${positionLabel}`,
    statusLabel: sourceBlocked ? "원천 근거 제한" : execution.statusLabel,
    statusTone: sourceBlocked ? "source_limited" : execution.statusTone,
    investmentImpact:
      kind === "fund_or_etf"
        ? "구성종목, 추적차이, 비용률, NAV 괴리와 시장 노출을 먼저 봅니다."
        : "가격, 재무 품질, 밸류에이션, 산업 위치, 뉴스와 사이클 근거를 함께 봅니다.",
    nextAction: sourceBlocked ? "원천 제한을 확인하고 투자 판단과 가상 검증 입력을 보류합니다." : execution.nextAction,
    sourceLimitReason: sourceBlocked
      ? recommendationCopy(data.professional_evidence_audit.source_blocker.blocker_code)
      : memoEvidenceAssessment(data.professional_evidence_audit).detail,
    metrics: [
      { label: "추천 점수", value: scoreLabel, context: "최종 점수 변경 없이 표시" },
      {
        label: "권고 비중",
        value: data.recommended_weight === null ? "비중 없음" : formatPercent(data.recommended_weight),
        context: "자동 주문에는 사용하지 않음",
      },
      { label: "상품 유형", value: recommendationProductLabel(kind), context: "분석 레이아웃 분기 기준" },
      { label: "포지션", value: positionLabel, context: data.position_context.portfolio_name },
    ],
  };
}
