import type { PaperTradingPreviewData } from "../types";

import { portfolioCopy } from "./investment-copy";
import { formatPercent } from "./format";
import type { DisplayStatusKind } from "./status";
import type { InvestmentViewModel } from "./view-model";

export type PaperTradingState = "execution_ready" | "safety_blocked" | "data_limited" | "approval_required" | "live_trading_disabled";

export function paperTradingState(data: PaperTradingPreviewData): PaperTradingState {
  if (!data.execution_boundary.broker_submit_allowed) {
    return "live_trading_disabled";
  }
  if (data.guardrails.length > 0) {
    return "safety_blocked";
  }
  if (data.quality_summary.requires_human_approval_count > 0) {
    return "approval_required";
  }
  if (data.quality_summary.unmeasured_recommendation_count > 0) {
    return "data_limited";
  }
  return "execution_ready";
}

export function paperTradingStateLabel(state: PaperTradingState): { readonly label: string; readonly tone: DisplayStatusKind } {
  if (state === "execution_ready") {
    return { label: "가상 검증 가능", tone: "ready" };
  }
  if (state === "safety_blocked") {
    return { label: "안전장치 차단", tone: "blocked" };
  }
  if (state === "data_limited") {
    return { label: "데이터 부족", tone: "source_limited" };
  }
  if (state === "approval_required") {
    return { label: "승인 필요", tone: "watch" };
  }
  return { label: "실거래 비활성", tone: "blocked" };
}

export function buildPaperTradingViewModel(data: PaperTradingPreviewData): InvestmentViewModel {
  const state = paperTradingState(data);
  const stateLabel = paperTradingStateLabel(state);

  return {
    title: `${data.portfolio_name} 가상 매매 검증`,
    summary: `${data.quality_summary.paper_action_count.toLocaleString("ko-KR")}개 검증 항목 · 적중률 ${
      data.quality_summary.hit_rate === null ? "미측정" : formatPercent(data.quality_summary.hit_rate)
    }`,
    statusLabel: stateLabel.label,
    statusTone: stateLabel.tone,
    investmentImpact: "추천 후보를 실제 주문으로 보내지 않고, 포지션 충돌과 안전 조건을 먼저 대조합니다.",
    nextAction:
      state === "execution_ready"
        ? "가상 검증 결과를 추천 상세와 포트폴리오 화면에서 대조합니다."
        : "차단 또는 부족 사유를 해소하기 전에는 주문 후보로 보지 않습니다.",
    sourceLimitReason: data.guardrails.length > 0 ? data.guardrails.map(portfolioCopy).join(" · ") : portfolioCopy(data.execution_boundary.order_boundary),
    metrics: [
      { label: "추천 후보", value: data.quality_summary.recommendation_count.toLocaleString("ko-KR"), context: "검증 대상" },
      { label: "가상 행동", value: data.quality_summary.paper_action_count.toLocaleString("ko-KR"), context: "실주문 아님" },
      { label: "충돌", value: data.quality_summary.position_recommendation_conflict_count.toLocaleString("ko-KR"), context: "보유와 추천 불일치" },
      { label: "실거래", value: data.execution_boundary.broker_submit_allowed ? "허용" : "차단", context: "주문 제출 경계" },
    ],
  };
}
