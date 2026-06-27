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
  if (brokerSubmitAllowed) {
    return styles.statusReady;
  }
  if (paperValidationAllowed) {
    return styles.statusWatch;
  }
  return styles.statusBlocked;
}

function productEvidenceLabel(productKind: RecommendationProductKind) {
  if (productKind === "fund_or_etf") {
    return "ETF·펀드 핵심";
  }
  return "기업 핵심";
}

function productEvidenceValue(productKind: RecommendationProductKind, counts: RecommendationHeaderCounts) {
  if (productKind === "fund_or_etf") {
    return counts.fundHoldingCount === null ? "보유 구성 대기" : `${counts.fundHoldingCount.toLocaleString("ko-KR")}개 보유 구성`;
  }
  return counts.financialMetricCount > 0 ? `${counts.financialMetricCount.toLocaleString("ko-KR")}개 재무 지표` : "재무 근거 대기";
}

function productEvidenceContext(productKind: RecommendationProductKind) {
  if (productKind === "fund_or_etf") {
    return "구성종목, 비용, NAV 괴리, 추적 품질이 판단의 중심이다.";
  }
  return "재무, 밸류에이션, 산업 위치를 뉴스와 사이클 근거와 분리한다.";
}

function productEvidenceHref(productKind: RecommendationProductKind) {
  if (productKind === "fund_or_etf") {
    return "#recommendation-fund-analysis";
  }
  return "#recommendation-financial-model";
}

export function RecommendationDecisionHeader({
  symbol,
  asOfDate,
  horizonLabel,
  recommendationLabel,
  positionStatusLabel,
  productKind,
  viewModel,
  counts,
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
        <h2 className={styles.mapTitle}>이 화면의 판단 순서</h2>
        <a className={styles.mapCardPrimary} href="#recommendation-professional-flow">
          <span>1. 추천 결론</span>
          <strong>{viewModel.investmentImpact}</strong>
          <small>{viewModel.nextAction}</small>
        </a>
        <a className={styles.mapCard} href="#recommendation-position-reality">
          <span>2. 포지션 현실</span>
          <strong>{positionStatusLabel}</strong>
          <small>보유 중이면 수량, 평단가, 평가손익이 판단의 출발점이다.</small>
        </a>
        <a className={counts.blockedStepCount > 0 ? styles.mapCardWatch : styles.mapCardReady} href="#recommendation-professional-flow">
          <span>3. 판단 단계</span>
          <strong>
            {counts.readyStepCount}/{counts.totalStepCount} 통과
          </strong>
          <small>
            주의 {counts.watchStepCount}개 · 차단 {counts.blockedStepCount}개
          </small>
        </a>
        <a className={styles.mapCardReady} href={productEvidenceHref(productKind)}>
          <span>4. {productEvidenceLabel(productKind)}</span>
          <strong>{productEvidenceValue(productKind, counts)}</strong>
          <small>{productEvidenceContext(productKind)}</small>
        </a>
        <a className={counts.marketCorrelationCount > 0 ? styles.mapCardReady : styles.mapCardWatch} href="#recommendation-market-correlations">
          <span>5. 시장 민감도</span>
          <strong>{counts.marketCorrelationCount.toLocaleString("ko-KR")}개 비교</strong>
          <small>지수, 금리, 달러, 원자재와 함께 움직인 정도를 보여준다.</small>
        </a>
        <a className={styles.mapCard} href="/paper-trading">
          <span>6. 실행 가능성</span>
          <strong>{execution.paperValidationAllowed ? "가상 검증 가능" : "가상 검증 차단"}</strong>
          <small>실거래 주문 제출은 별도 승인 전까지 차단한다.</small>
        </a>
      </nav>
    </section>
  );
}
