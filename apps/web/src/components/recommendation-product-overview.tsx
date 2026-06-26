import { koCode } from "@/lib/korean-labels";
import { recommendationCopy } from "@/lib/presentation";
import type { RecommendationDetailData } from "@/lib/types";

import styles from "../app/recommendations/[recommendationId]/RecommendationDetailPage.module.css";

export type RecommendationProductProfile = {
  kind: "fund_or_etf" | "company";
  label: string;
  headline: string;
  primaryLens: string;
  secondaryLens: string;
  evidenceTitle: string;
};

export type RecommendationQualityDecision = {
  status: string;
  tone: "risk-low" | "risk-medium" | "risk-high";
  summary: string;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatOptionalPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "산출 대기";
  }
  return formatPercent(value);
}

function formatCurrency(value: number | null | undefined, currencyCode: string) {
  if (value === null || value === undefined) {
    return "금액 대기";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatCompactNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "수치 대기";
  }
  return new Intl.NumberFormat("ko-KR", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatExpenseRatio(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "비용률 대기";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 4,
  })}%`;
}

function fundStatusLabel(value: string) {
  if (value === "available" || value === "collected") {
    return "원천 연결";
  }
  if (value === "not_applicable") {
    return "비적용";
  }
  return recommendationCopy(value);
}

function competitivePositionLabel(value: string) {
  const labels: Record<string, string> = {
    leader: "경쟁 우위",
    advantaged: "우위 후보",
    in_line: "평균권",
    challenged: "열위 검토",
    insufficient_data: "데이터 부족",
  };
  return labels[value] ?? koCode(value);
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "거래 경계 대기";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 차단";
  }
  return recommendationCopy(value);
}

export function RecommendationProductOverview({
  data,
  productProfile,
  qualityDecision,
  decisionWaterfall,
}: {
  data: RecommendationDetailData;
  productProfile: RecommendationProductProfile;
  qualityDecision: RecommendationQualityDecision;
  decisionWaterfall: RecommendationDetailData["professional_decision_waterfall"];
}) {
  const fundAnalysis = data.fund_instrument_analysis;
  const position = data.position_context;
  const held = position.status === "held";
  const positionTitle = held ? "보유 중" : "현재 미보유";
  const averageCostText = held ? formatCurrency(position.average_cost, position.currency_code) : "평단가 없음";
  const marketValueText = held ? formatCurrency(position.market_value, position.currency_code) : "보유금액 없음";
  const leadCopy =
    productProfile.kind === "fund_or_etf"
      ? "ETF·펀드는 보유종목 구성, 벤치마크 추적, 비용률, NAV 괴리, 유동성으로 보유 품질을 판단한다."
      : "개별 기업은 재무 품질, 밸류에이션, 산업 내 위치, 투자 논리와 포지션 현실을 함께 판단한다.";

  return (
    <section className={styles.productOverview} aria-label="추천 상품 유형과 핵심 판단">
      <div className={styles.productLead}>
        <span>{productProfile.label}</span>
        <h2>{productProfile.headline}</h2>
        <p>{leadCopy}</p>
      </div>

      <div className={styles.productSummaryGrid}>
        <article className={styles.productMetric}>
          <span>현재 결론</span>
          <strong>{qualityDecision.status}</strong>
          <p>{qualityDecision.summary}</p>
        </article>
        <article className={styles.productMetric}>
          <span>추천 점수</span>
          <strong>{formatPercent(data.score)}</strong>
          <p>권고 비중 {formatOptionalPercent(data.recommended_weight)} · {koCode(data.recommendation)}</p>
        </article>
        <article className={styles.productMetric}>
          <span>포지션·평단가</span>
          <strong>{positionTitle}</strong>
          <p>
            {averageCostText} · {marketValueText}
            {position.summary ? ` · ${position.summary}` : ""}
          </p>
        </article>
        <article className={styles.productMetric}>
          <span>거래 경계</span>
          <strong>{orderBoundaryLabel(decisionWaterfall.order_boundary)}</strong>
          <p>
            가상 매매 {decisionWaterfall.paper_validation_input_allowed ? "입력 가능" : "입력 차단"} · 실거래{" "}
            {decisionWaterfall.broker_submit_allowed ? "허용" : "차단"}
          </p>
        </article>
      </div>

      {productProfile.kind === "fund_or_etf" && fundAnalysis ? (
        <div className={styles.productEvidenceGrid} aria-label="ETF 추천 핵심 근거">
          <article>
            <span>구성</span>
            <strong>{fundAnalysis.holding_count.toLocaleString("ko-KR")}개 보유종목</strong>
            <p>
              커버리지 {formatOptionalPercent(fundAnalysis.holdings_coverage_weight)} · 벤치마크{" "}
              {fundAnalysis.benchmark_code || data.symbol}
            </p>
          </article>
          <article>
            <span>비용</span>
            <strong>{formatExpenseRatio(fundAnalysis.expense_ratio.value)}</strong>
            <p>{fundAnalysis.expense_ratio.source_name ? recommendationCopy(fundAnalysis.expense_ratio.source_name) : "공식 원천"} · {fundAnalysis.expense_ratio.source_as_of_date || "기준일 대기"}</p>
          </article>
          <article>
            <span>추적 품질</span>
            <strong>
              {fundAnalysis.tracking_error.metric_type === "tracking_difference"
                ? formatOptionalPercent(fundAnalysis.tracking_error.tracking_difference_value)
                : koCode(fundAnalysis.tracking_error.status)}
            </strong>
            <p>{fundAnalysis.tracking_error.measurement_window || "기간 대기"} · {fundAnalysis.tracking_error.benchmark_name || "벤치마크 대기"}</p>
          </article>
          <article>
            <span>NAV 괴리</span>
            <strong>{formatOptionalPercent(fundAnalysis.nav_premium_discount.premium_discount_to_nav)}</strong>
            <p>
              NAV {formatCurrency(fundAnalysis.nav_premium_discount.nav_per_share, data.currency_code)} · 종가{" "}
              {formatCurrency(fundAnalysis.nav_premium_discount.closing_price, data.currency_code)}
            </p>
          </article>
          <article>
            <span>유동성</span>
            <strong>{fundStatusLabel(fundAnalysis.liquidity.status)}</strong>
            <p>
              평균 거래량 {formatCompactNumber(fundAnalysis.liquidity.average_daily_volume)} · 평균 거래대금{" "}
              {formatCurrency(fundAnalysis.liquidity.average_daily_dollar_volume, data.currency_code)}
            </p>
          </article>
          <article>
            <span>상위 보유</span>
            <strong>{fundAnalysis.top_holdings.slice(0, 3).map((holding) => holding.symbol).join(" · ") || "구성 대기"}</strong>
            <p>{fundAnalysis.portfolio_role.rationale || "포트폴리오 역할 설명 대기"}</p>
          </article>
        </div>
      ) : (
        <div className={styles.productEvidenceGrid} aria-label="개별 기업 추천 핵심 근거">
          <article>
            <span>재무 모델</span>
            <strong>{data.financial_statement_model.status === "available" ? "연결" : koCode(data.financial_statement_model.status)}</strong>
            <p>{data.financial_statement_model.computed_metric_count.toLocaleString("ko-KR")}개 지표 · {data.financial_statement_model.latest_period_end || "기간 대기"}</p>
          </article>
          <article>
            <span>밸류에이션</span>
            <strong>{data.valuation_target_range.status === "available" ? "목표 범위 연결" : koCode(data.valuation_target_range.status)}</strong>
            <p>
              상승여지 {formatOptionalPercent(data.valuation_target_range.upside_base)} · 안전마진{" "}
              {formatOptionalPercent(data.valuation_target_range.margin_of_safety)}
            </p>
          </article>
          <article>
            <span>산업 위치</span>
            <strong>
              {data.industry_competitive_position
                ? competitivePositionLabel(data.industry_competitive_position.competitive_position)
                : "비교군 대기"}
            </strong>
            <p>{data.industry_competitive_position?.peer_group_name ?? "비교군 데이터 보강 대기"}</p>
          </article>
        </div>
      )}
    </section>
  );
}
