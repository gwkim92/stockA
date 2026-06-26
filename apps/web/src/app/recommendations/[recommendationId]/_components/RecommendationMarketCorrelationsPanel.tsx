import Link from "next/link";

import type { RecommendationDetailData } from "@/lib/types";

import { formatPanelOptionalPercent } from "./recommendation-panel-format";

type RecommendationMarketCorrelation = RecommendationDetailData["market_correlations"][number];

type RecommendationMarketCorrelationsPanelProps = {
  readonly symbol: string;
  readonly correlations: readonly RecommendationMarketCorrelation[];
};

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

function correlationTone(correlation: RecommendationMarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

export function RecommendationMarketCorrelationsPanel({
  symbol,
  correlations,
}: RecommendationMarketCorrelationsPanelProps) {
  return (
    <section className="bento-card reveal delay-1" id="recommendation-market-correlations" aria-label="추천 시장 동조성 리스크">
      <div className="section-heading">
        <div>
          <span className="metric-sub">시장 동조성 리스크</span>
          <h2>{symbol} 추천과 같이 움직인 시장 변수</h2>
        </div>
        <Link className="btn btn-secondary" href="/market-map">
          시장 지도 보기
        </Link>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        이 섹션은 추천 점수를 새로 만들지 않는다. 최근 수익률 동조성을 이용해 같은 방향으로 몰린 리스크,
        헤지 필요성과 포트폴리오 집중 위험을 함께 제시합니다. 상관관계는 원인을 증명하지 않습니다.
      </p>
      {correlations.length > 0 ? (
        <div className="detail-path-grid">
          {correlations.slice(0, 6).map((correlation) => (
            <article
              className={correlationTone(correlation)}
              key={`${correlation.primary_asset_key}-${correlation.comparison_asset_key}-${correlation.lookback_days}`}
            >
              <span>
                {correlationRelationshipLabel(correlation.relationship_label)} · {correlation.lookback_days}일 · 신뢰도{" "}
                {formatPanelOptionalPercent(correlation.confidence)}
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
          아직 이 추천 종목의 시장 동조성이 계산되지 않았다. 상관관계 분석이 실행되면 추천 리스크 확인용으로 표시된다.
        </div>
      )}
    </section>
  );
}
