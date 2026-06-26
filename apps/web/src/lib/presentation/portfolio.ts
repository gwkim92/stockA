import type { PortfolioCoverageData } from "../types";

import { portfolioCopy } from "./investment-copy";
import { calculatePortfolioReturnSummary, formatSignedPercent } from "./returns";
import type { InvestmentViewModel } from "./view-model";

export function buildPortfolioCoverageViewModel(data: PortfolioCoverageData): InvestmentViewModel {
  const returns = calculatePortfolioReturnSummary(data.positions);
  const returnLabel = formatSignedPercent(returns.returnPct, { metricLabel: "포트폴리오 수익률" });
  const largestPosition = data.risk_budget.largest_position_symbol ?? "상위 종목 없음";

  return {
    title: `${data.portfolio_name} 포트폴리오 상태`,
    summary: `${data.summary.position_count.toLocaleString("ko-KR")}개 포지션 · 수익률 ${returnLabel.label} · 최대 비중 ${largestPosition}`,
    statusLabel: data.risk_budget.over_single_position_limit_count > 0 ? "집중도 점검" : "한도 내",
    statusTone: data.risk_budget.over_single_position_limit_count > 0 ? "watch" : "ready",
    investmentImpact: "평단가, 평가손익, 수익률, 벤치마크 괴리와 thesis 연결 상태를 함께 봅니다.",
    nextAction:
      data.risk_budget.over_single_position_limit_count > 0
        ? "한도 초과 종목의 thesis와 리밸런싱 후보를 먼저 봅니다."
        : "성과 측정 성숙도와 벤치마크 괴리만 정기적으로 확인합니다.",
    sourceLimitReason: portfolioCopy(data.risk_budget.status),
    metrics: [
      { label: "평가금액", value: returns.marketValue === null ? "미측정" : returns.marketValue.toLocaleString("ko-KR"), context: data.base_currency },
      { label: "평가손익", value: returns.unrealizedPnl === null ? "미측정" : returns.unrealizedPnl.toLocaleString("ko-KR"), context: "보유 포지션 합산" },
      { label: "수익률", value: returnLabel.label, context: returnLabel.a11yLabel },
      { label: "연결 상태", value: `${Math.round(data.summary.weight_coverage_ratio * 100)}%`, context: "thesis·성과 연결 비중" },
    ],
  };
}
