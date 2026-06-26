import type { RecommendationDetailData } from "@/lib/types";

import {
  formatPanelCompactNumber,
  formatPanelCurrency,
  formatPanelExpenseRatio,
  formatPanelFundCurrency,
  formatPanelOptionalPercent,
  fundPanelStatusLabel,
  recommendationPanelOrderBoundaryLabel,
  userFacingRecommendationText,
} from "./recommendation-panel-format";

type FundInstrumentAnalysis = RecommendationDetailData["fund_instrument_analysis"];

type RecommendationFundInstrumentAnalysisPanelProps = {
  readonly analysis: FundInstrumentAnalysis;
};

export function RecommendationFundInstrumentAnalysisPanel({ analysis }: RecommendationFundInstrumentAnalysisPanelProps) {
  if (!analysis) {
    return null;
  }
  return (
    <section className="bento-card reveal delay-1" aria-label="추천 ETF와 펀드형 상품 분석">
      <div style={{ marginBottom: "18px" }}>
        <span className="metric-sub">ETF·펀드 추천 근거</span>
        <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>
          ETF·펀드 상품 분석: {analysis.symbol}
        </h2>
        <p style={{ color: "var(--text-secondary)", marginTop: "8px" }}>
          {analysis.summary}
        </p>
      </div>
      <div className="status-rail compact-rail" aria-label="추천 ETF와 펀드형 상품 분석 요약">
        <div className="rail-cell">
          <span>벤치마크</span>
          <strong>{analysis.benchmark_code || analysis.symbol}</strong>
          <small>{analysis.benchmark_source ? userFacingRecommendationText(analysis.benchmark_source) : "원천 미확인"}</small>
        </div>
        <div className="rail-cell">
          <span>구성 커버리지</span>
          <strong>{formatPanelOptionalPercent(analysis.holdings_coverage_weight)}</strong>
          <small>{analysis.holding_count.toLocaleString("ko-KR")}개 보유종목</small>
        </div>
        <div className="rail-cell">
          <span>현재 비중</span>
          <strong>{formatPanelOptionalPercent(analysis.portfolio_role.current_weight)}</strong>
          <small>{analysis.portfolio_role.portfolio_name}</small>
        </div>
        <div className="rail-cell">
          <span>추천 비중</span>
          <strong>{formatPanelOptionalPercent(analysis.portfolio_role.recommended_weight)}</strong>
          <small>읽기 전용</small>
        </div>
      </div>
      <div className="detail-grid" style={{ marginTop: "18px" }}>
        {analysis.top_holdings.slice(0, 6).map((holding) => (
          <article className="detail-path-card" key={`fund-holding-${holding.symbol}`}>
            <span>{holding.symbol}</span>
            <strong>{holding.name || holding.symbol}</strong>
            <p>보유 비중 {formatPanelOptionalPercent(holding.target_weight)} · 자료 신뢰도 {formatPanelOptionalPercent(holding.confidence)}</p>
          </article>
        ))}
      </div>
      <div className="flow-steps" style={{ marginTop: "18px" }}>
        <article className="flow-step">
          <span>추적오차/추적차이</span>
          <strong>
            {analysis.tracking_error.metric_type === "tracking_difference"
              ? formatPanelOptionalPercent(analysis.tracking_error.tracking_difference_value)
              : fundPanelStatusLabel(analysis.tracking_error.status)}
          </strong>
          <p>
            {userFacingRecommendationText(analysis.tracking_error.summary)}
            {analysis.tracking_error.measurement_window
              ? ` 기간 ${analysis.tracking_error.measurement_window}`
              : ""}
            {analysis.tracking_error.benchmark_name ? ` · 기준 ${analysis.tracking_error.benchmark_name}` : ""}
            {analysis.tracking_error.fund_return !== null
              ? ` · NAV 수익률 ${formatPanelOptionalPercent(analysis.tracking_error.fund_return)}`
              : ""}
            {analysis.tracking_error.benchmark_return !== null
              ? ` · 벤치마크 ${formatPanelOptionalPercent(analysis.tracking_error.benchmark_return)}`
              : ""}
          </p>
          {analysis.tracking_error.source_url ? (
            <a href={analysis.tracking_error.source_url} target="_blank" rel="noreferrer">
              추적차이 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>비용률</span>
          <strong>{formatPanelExpenseRatio(analysis.expense_ratio.value)}</strong>
          <p>
            {userFacingRecommendationText(analysis.expense_ratio.summary)} 상태 {fundPanelStatusLabel(analysis.expense_ratio.status)}
            {analysis.expense_ratio.source_name ? ` · 원천 ${userFacingRecommendationText(analysis.expense_ratio.source_name)}` : ""}
            {analysis.expense_ratio.source_as_of_date ? ` · 기준일 ${analysis.expense_ratio.source_as_of_date}` : ""}
          </p>
          {analysis.expense_ratio.source_url ? (
            <a href={analysis.expense_ratio.source_url} target="_blank" rel="noreferrer">
              비용률 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>NAV 괴리</span>
          <strong>{formatPanelOptionalPercent(analysis.nav_premium_discount.premium_discount_to_nav)}</strong>
          <p>
            {userFacingRecommendationText(analysis.nav_premium_discount.summary)} NAV {formatPanelFundCurrency(analysis.nav_premium_discount.nav_per_share, "USD")} ·
            종가 {formatPanelFundCurrency(analysis.nav_premium_discount.closing_price, "USD")}
            {analysis.nav_premium_discount.premium_discount_as_of_date
              ? ` · 기준일 ${analysis.nav_premium_discount.premium_discount_as_of_date}`
              : ""}
          </p>
          {analysis.nav_premium_discount.source_url ? (
            <a href={analysis.nav_premium_discount.source_url} target="_blank" rel="noreferrer">
              NAV 원천 열기
            </a>
          ) : null}
        </article>
        <article className="flow-step">
          <span>유동성</span>
          <strong>{fundPanelStatusLabel(analysis.liquidity.status)}</strong>
          <p>
            {userFacingRecommendationText(analysis.liquidity.summary)} 평균 거래량 {formatPanelCompactNumber(analysis.liquidity.average_daily_volume)} ·
            평균 거래대금 {formatPanelCurrency(analysis.liquidity.average_daily_dollar_volume, "USD")}
          </p>
        </article>
        <article className="flow-step">
          <span>실거래 상태</span>
          <strong>{recommendationPanelOrderBoundaryLabel(analysis.order_boundary)}</strong>
          <p>펀드 분석은 추천 점수와 주문 가능 여부를 자동 변경하지 않는다.</p>
        </article>
      </div>
    </section>
  );
}
