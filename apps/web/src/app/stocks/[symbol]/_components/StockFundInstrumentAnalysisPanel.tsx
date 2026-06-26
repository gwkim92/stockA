import type { StockDetailData } from "@/lib/types";

import {
  formatCompactNumber,
  formatCurrency,
  formatPercent,
  fundStatusLabel,
  stockSourceLabel,
  stockText,
} from "./stock-detail-panel-format";

type FundInstrumentAnalysis = StockDetailData["fund_instrument_analysis"];

type StockFundInstrumentAnalysisPanelProps = {
  readonly analysis: FundInstrumentAnalysis;
};

export function StockFundInstrumentAnalysisPanel({ analysis }: StockFundInstrumentAnalysisPanelProps) {
  if (!analysis) {
    return null;
  }

  return (
    <section className="bento-card span-4 reveal delay-2" id="stock-fund-analysis" aria-label="ETF와 펀드형 상품 분석">
      <div className="section-heading">
        <div>
          <span className="metric-sub">ETF·펀드 분석</span>
          <h2>{analysis.symbol}은 기업 재무제표가 아니라 보유종목과 노출도로 본다</h2>
        </div>
        <span className="bento-badge" style={{ margin: 0 }}>{fundStatusLabel(analysis.status)}</span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>{analysis.summary}</p>
      <div className="status-rail compact-rail" aria-label="ETF와 펀드형 상품 분석 요약">
        <div className="rail-cell">
          <span>벤치마크</span>
          <strong>{analysis.benchmark_code || analysis.symbol}</strong>
          <small>{stockSourceLabel(analysis.benchmark_source)}</small>
        </div>
        <div className="rail-cell">
          <span>보유종목 커버리지</span>
          <strong>{formatPercent(analysis.holdings_coverage_weight)}</strong>
          <small>{analysis.holding_count.toLocaleString("ko-KR")}개 구성종목</small>
        </div>
        <div className="rail-cell">
          <span>현재 포트폴리오 비중</span>
          <strong>{formatPercent(analysis.portfolio_role.current_weight)}</strong>
          <small>{analysis.portfolio_role.portfolio_name}</small>
        </div>
        <div className="rail-cell">
          <span>추천 목표 비중</span>
          <strong>{formatPercent(analysis.portfolio_role.recommended_weight)}</strong>
          <small>주문 자동 생성 없음</small>
        </div>
      </div>
      <div className="relationship-panel" aria-label="상위 보유종목">
        <span>상위 보유종목</span>
        <div className="relationship-list">
          {analysis.top_holdings.slice(0, 6).map((holding) => (
            <div className="relationship-chip" key={holding.symbol}>
              <span>{holding.symbol}</span>
              <strong>{holding.name || holding.symbol}</strong>
              <small>
                목표 비중 {formatPercent(holding.target_weight)} · 신뢰도 {formatPercent(holding.confidence)}
              </small>
            </div>
          ))}
          {analysis.top_holdings.length === 0 ? (
            <p className="relationship-empty">보유종목 원천이 아직 연결되지 않았다.</p>
          ) : null}
        </div>
      </div>
      <div className="flow-steps">
        <article className="flow-step">
          <span>추적오차/추적차이</span>
          <strong>
            {analysis.tracking_error.metric_type === "tracking_difference"
              ? formatPercent(analysis.tracking_error.tracking_difference_value)
              : fundStatusLabel(analysis.tracking_error.status)}
          </strong>
          <p>
            {stockText(analysis.tracking_error.summary)}
            {analysis.tracking_error.measurement_window ? ` 기간 ${analysis.tracking_error.measurement_window}` : ""}
            {analysis.tracking_error.benchmark_name ? ` · 기준 ${analysis.tracking_error.benchmark_name}` : ""}
            {analysis.tracking_error.fund_return !== null ? ` · NAV 수익률 ${formatPercent(analysis.tracking_error.fund_return)}` : ""}
            {analysis.tracking_error.benchmark_return !== null
              ? ` · 벤치마크 ${formatPercent(analysis.tracking_error.benchmark_return)}`
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
          <strong>{formatPercent(analysis.expense_ratio.value)}</strong>
          <p>
            {stockText(analysis.expense_ratio.summary)} 상태 {fundStatusLabel(analysis.expense_ratio.status)}
            {analysis.expense_ratio.source_name ? ` · 원천 ${stockSourceLabel(analysis.expense_ratio.source_name)}` : ""}
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
          <strong>{formatPercent(analysis.nav_premium_discount.premium_discount_to_nav)}</strong>
          <p>
            {stockText(analysis.nav_premium_discount.summary)} NAV {formatCurrency(analysis.nav_premium_discount.nav_per_share, "USD")} ·
            종가 {formatCurrency(analysis.nav_premium_discount.closing_price, "USD")}
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
          <strong>{fundStatusLabel(analysis.liquidity.status)}</strong>
          <p>
            {stockText(analysis.liquidity.summary)} 평균 거래량 {formatCompactNumber(analysis.liquidity.average_daily_volume)} ·
            평균 거래대금 {formatCurrency(analysis.liquidity.average_daily_dollar_volume, "USD")}
          </p>
        </article>
        <article className="flow-step">
          <span>실거래 상태</span>
          <strong>{stockSourceLabel(analysis.order_boundary)}</strong>
          <p>이 분석은 추천 점수와 주문 가능 여부를 자동 변경하지 않는다.</p>
        </article>
      </div>
    </section>
  );
}
