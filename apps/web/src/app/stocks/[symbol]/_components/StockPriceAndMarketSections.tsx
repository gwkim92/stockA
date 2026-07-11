import Link from "next/link";

import { CandlestickChart } from "@/components/candlestick-chart";
import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import { koCode } from "@/lib/korean-labels";
import { brokerDataUseLabel, formatBasisPointDiff, stockCopy } from "@/lib/presentation";
import type { StockDetailData } from "@/lib/types";

import { formatCurrency, formatPercent } from "./stock-detail-panel-format";
import styles from "./StockPriceAndMarketSections.module.css";

type StockMarketCorrelation = StockDetailData["market_correlations"][number];

type StockPriceAndMarketSectionsProps = {
  readonly data: StockDetailData;
  readonly latestChangePct: number | null;
};

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return value.toLocaleString("ko-KR");
}

function userFacingStockText(value: string | null | undefined) {
  return stockCopy(value);
}

function priceSourceProviderLabel(value: string | null | undefined) {
  if (!value || value.toLowerCase() === "missing") {
    return "원천 대기";
  }
  return userFacingStockText(koCode(value));
}

function compactTossComparisonLabel(value: string) {
  if (value.includes("비교 완료")) {
    return "비교 완료";
  }
  if (value.includes("검토")) {
    return "차이 검토";
  }
  if (value.includes("대기")) {
    return "비교 대기";
  }
  return value;
}

function formatCoefficient(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format(value);
}

function correlationRelationshipLabel(label: string) {
  if (label === "strong_positive") {
    return "강한 동행";
  }
  if (label === "strong_negative") {
    return "강한 반대";
  }
  if (label === "moderate_positive") {
    return "보통 동행";
  }
  if (label === "moderate_negative") {
    return "보통 반대";
  }
  return "약하거나 불명확";
}

function correlationTone(correlation: StockMarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

export function StockPriceAndMarketSections({ data, latestChangePct }: StockPriceAndMarketSectionsProps) {
  return (
    <>
      <section className="bento-grid reveal delay-2" id="stock-price-data" aria-label="가격 데이터와 차트">
        <article className="bento-card span-3">
          <div className="section-heading">
            <div>
              <span className="metric-sub">가격 데이터</span>
              <h2>가격 흐름은 데이터 출처와 추세가 먼저다</h2>
            </div>
            <Link className="btn btn-secondary" href="/data-health">
              수집 상태 보기
            </Link>
          </div>
          <CandlestickChart
            bars={data.candles}
            currencyCode={data.currency_code}
            provider={data.market_data_provider}
            tossEvidence={data.toss_provider_evidence}
          />
        </article>

        <article className={`bento-card ${styles.priceSummary}`}>
          <div className={styles.priceSummaryLead}>
            <span className="metric-label">가격 데이터</span>
            <strong className="metric-value">{data.summary.bar_count.toLocaleString("ko-KR")}</strong>
            <span className="metric-sub">수집된 거래일 수</span>
          </div>
          <div className="stock-meta-grid">
            <span>저가 종가</span>
            <strong>{formatCurrency(data.summary.low_close, data.currency_code)}</strong>
            <span>고가 종가</span>
            <strong>{formatCurrency(data.summary.high_close, data.currency_code)}</strong>
            <span>거래량</span>
            <strong>{formatNumber(data.latest_price.volume)}</strong>
            <span>전일 대비</span>
            <strong>
              <SignedReturnBadge value={latestChangePct} />
            </strong>
          </div>
          <div className="stock-meta-grid">
            <span>분석 기준</span>
            <strong>{priceSourceProviderLabel(data.market_data_provider.analysis_price_source.provider)}</strong>
            <span>계산 반영</span>
            <strong>{data.market_data_provider.analysis_price_source.used_for_scoring ? "추천·사이클 사용" : "미사용"}</strong>
            <span>브로커 참고</span>
            <strong>{data.market_data_provider.broker_price_source.label}</strong>
            <span>토스 상태</span>
            <strong>{compactTossComparisonLabel(data.toss_provider_evidence.comparison.status_label)}</strong>
          </div>
          <p className={styles.priceSummaryCopy}>
            {stockCopy(data.market_data_provider.price_basis_note)} 토스증권 가격은 계좌·호가 현실 확인용이며 총점에는 아직 반영하지 않는다.
          </p>
        </article>

        <article className={`bento-card span-4 ${styles.broker}`}>
          <div className={styles.brokerSummary}>
            <span className="metric-label">토스증권 브로커 현실</span>
            <strong className="metric-value">{data.toss_provider_evidence.status_label}</strong>
            <span className="metric-sub">
              {brokerDataUseLabel(data.toss_provider_evidence)} · {data.toss_provider_evidence.comparison.status_label}
            </span>
          </div>
          <div className={styles.brokerMetrics}>
            <div className="stock-meta-grid">
              <span>토스 기준일</span>
              <strong>{data.toss_provider_evidence.latest_trade_date || "기준일 대기"}</strong>
              <span>토스 종가</span>
              <strong>{formatCurrency(data.toss_provider_evidence.latest_close, data.currency_code)}</strong>
              <span>토스 거래량</span>
              <strong>{formatNumber(data.toss_provider_evidence.latest_volume)}</strong>
              <span>비교일</span>
              <strong>{data.toss_provider_evidence.comparison.comparison_date || "비교 대기"}</strong>
            </div>
            <div className="stock-meta-grid">
              <span>비교 봉</span>
              <strong>{formatNumber(data.toss_provider_evidence.comparison.matched_bar_count)}</strong>
              <span>중앙 차이</span>
              <strong>{formatBasisPointDiff(data.toss_provider_evidence.comparison.median_close_diff_bps)}</strong>
              <span>최대 차이</span>
              <strong>{formatBasisPointDiff(data.toss_provider_evidence.comparison.max_close_diff_bps)}</strong>
              <span>추천 반영</span>
              <strong>{data.toss_provider_evidence.used_for_scoring ? "반영 중" : "미반영"}</strong>
            </div>
          </div>
          <p className={styles.brokerCopy}>
            {stockCopy(data.toss_provider_evidence.price_basis_note)} 토스와 글로벌 가격이 다를 수 있으므로 차이를 오류로
            단정하지 않고 계좌 현실, 가격 기준 차이, 미완성 최신 일봉 여부를 따로 본다.
          </p>
        </article>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="stock-market-correlations" aria-label="시장 동조성">
        <div className="section-heading">
          <div>
            <span className="metric-sub">시장 동조성</span>
            <h2>{data.symbol}과 같이 움직인 시장 변수</h2>
          </div>
          <Link className="btn btn-secondary" href="/market-map">
            시장 지도 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          상관관계는 최근 수익률이 같이 움직인 정도다. 원인을 단정하지 않고, 포트폴리오 집중·헤지 필요성·추천 리스크의 보조 입력으로만 사용한다.
        </p>
        {data.market_correlations.length > 0 ? (
          <div className="detail-path-grid">
            {data.market_correlations.slice(0, 6).map((correlation) => (
              <article
                className={correlationTone(correlation)}
                key={`${correlation.primary_asset_key}-${correlation.comparison_asset_key}-${correlation.lookback_days}`}
              >
                <span>
                  {correlationRelationshipLabel(correlation.relationship_label)} · {correlation.lookback_days}일 · 신뢰도{" "}
                  {formatPercent(correlation.confidence)}
                </span>
                <strong>
                  {correlation.primary_display_name} ↔ {correlation.comparison_display_name}
                </strong>
                <small>
                  상관계수 {formatCoefficient(correlation.correlation)} · 베타 {formatCoefficient(correlation.beta)} · 관측{" "}
                  {correlation.observation_count.toLocaleString("ko-KR")}개
                </small>
                <p>{correlation.summary_ko}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 이 종목의 시장 동조성이 계산되지 않았다. 장마감 후 상관관계 분석이 실행되면 지수·섹터·금리·달러·원자재와의 관계가 표시된다.
          </div>
        )}
      </section>
    </>
  );
}
