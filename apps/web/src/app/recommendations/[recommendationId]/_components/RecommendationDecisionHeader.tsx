import type { InvestmentViewModel, RecommendationProductKind } from "@/lib/presentation";

import styles from "./RecommendationDecisionHeader.module.css";

type RecommendationHeaderCounts = {
  readonly readyStepCount: number;
  readonly watchStepCount: number;
  readonly blockedStepCount: number;
  readonly totalStepCount: number;
  readonly marketCorrelationCount: number;
  readonly financialMetricCount: number;
  readonly fundHoldingCount: number | null;
};

type RecommendationExecution = {
  readonly paperValidationAllowed: boolean;
  readonly brokerSubmitAllowed: boolean;
  readonly orderStatusLabel: string;
};

type RecommendationDecisionHeaderProps = {
  readonly symbol: string;
  readonly asOfDate: string;
  readonly horizonLabel: string;
  readonly recommendationLabel: string;
  readonly positionStatusLabel: string;
  readonly productKind: RecommendationProductKind;
  readonly viewModel: InvestmentViewModel;
  readonly counts: RecommendationHeaderCounts;
  readonly execution: RecommendationExecution;
};

function executionStatusClass({ paperValidationAllowed, brokerSubmitAllowed }: RecommendationExecution) {
  if (brokerSubmitAllowed) return styles.statusReady;
  if (paperValidationAllowed) return styles.statusWatch;
  return styles.statusBlocked;
}

function productEvidenceLabel(productKind: RecommendationProductKind) {
  return productKind === "fund_or_etf" ? "ETF·펀드 핵심" : "기업 핵심";
}

function productEvidenceContext(productKind: RecommendationProductKind) {
  return productKind === "fund_or_etf"
    ? "구성종목, 비용, NAV 괴리, 추적 품질이 판단의 중심이다."
    : "재무, 밸류에이션, 산업 위치를 뉴스와 사이클 근거와 분리한다.";
}

function productEvidenceHref(productKind: RecommendationProductKind) {
  return productKind === "fund_or_etf" ? "#recommendation-fund-analysis" : "#recommendation-financial-model";
}

export function RecommendationDecisionHeader({
  symbol,
  asOfDate,
  horizonLabel,
  recommendationLabel,
  positionStatusLabel,
  productKind,
  viewModel,
  execution,
}: RecommendationDecisionHeaderProps) {
  const executionClassName = executionStatusClass(execution);
  const productLabel = productKind === "fund_or_etf" ? "ETF·펀드" : "개별 기업";

  return (
    <section className={styles.header} aria-labelledby="recommendation-detail-title">
      <div className={styles.narrative}>
        <span className={styles.eyebrow}>
          추천 리포트 · {productLabel} · {horizonLabel} · {asOfDate}
        </span>
        <h1 className={styles.title} id="recommendation-detail-title">
          {symbol} 추천 판단서
        </h1>
        <p className={styles.summary}>{viewModel.summary}</p>
        <p className={styles.summary}>{productEvidenceContext(productKind)}</p>
        <div className={styles.statusLine} aria-label="추천 상세 핵심 상태">
          <span className={styles.status}>{viewModel.statusLabel}</span>
          <span className={styles.status}>추천 {recommendationLabel}</span>
          <span className={styles.status}>포지션 {positionStatusLabel}</span>
          <span className={executionClassName}>{execution.orderStatusLabel}</span>
        </div>
        <div className={styles.metricGrid} aria-label="추천 상세 핵심 지표">
          {viewModel.metrics.map((metric) => (
            <article className={styles.metric} key={metric.label}>
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
              <small>{metric.context}</small>
            </article>
          ))}
        </div>
      </div>

      <nav className={styles.map} aria-label="추천 상세 읽는 순서">
        <a href="#recommendation-investment-memo" className={styles.mapCardPrimary}>01 투자 판단서</a>
        <a href="#recommendation-position-reality" className={styles.mapCard}>02 보유 점검</a>
        <a href={productEvidenceHref(productKind)} className={styles.mapCard}>03 {productEvidenceLabel(productKind)}</a>
        <a href="#recommendation-market-correlations" className={styles.mapCard}>04 시장 민감도</a>
        <a href="#recommendation-professional-flow" className={styles.mapCard}>05 분석 단계</a>
      </nav>
    </section>
  );
}
