import type { Route } from "next";
import Link from "next/link";

import { SignedReturnBadge } from "@/components/research/SignedReturnBadge";
import type { InvestmentViewModel, StockProductKind } from "@/lib/presentation";

import styles from "./StockResearchHeader.module.css";

type StockHeaderPrice = {
  readonly priceLabel: string;
  readonly changePct: number | null;
  readonly priceSourceLabel: string;
};

type StockHeaderPosition = {
  readonly statusLabel: string;
  readonly quantityLabel: string;
  readonly averageCostLabel: string;
  readonly unrealizedPnlLabel: string;
};

type StockHeaderRecommendation = {
  readonly href: Route | null;
  readonly label: string;
  readonly context: string;
};

type StockHeaderCounts = {
  readonly stockNewsCount: number;
  readonly directNewsCount: number;
  readonly macroFlowCount: number;
  readonly marketCorrelationCount: number;
  readonly financialMetricCount: number;
  readonly fundHoldingCount: number | null;
};

type StockResearchHeaderProps = {
  readonly symbol: string;
  readonly name: string;
  readonly marketCode: string;
  readonly asOfDate: string;
  readonly productKind: StockProductKind;
  readonly sourceBlocked: boolean;
  readonly linkedThesisHref: Route | null;
  readonly viewModel: InvestmentViewModel;
  readonly price: StockHeaderPrice;
  readonly position: StockHeaderPosition;
  readonly recommendation: StockHeaderRecommendation;
  readonly counts: StockHeaderCounts;
};

function statusClassName(sourceBlocked: boolean, hasRecommendation: boolean) {
  if (sourceBlocked) {
    return styles.statusBlocked;
  }
  if (hasRecommendation) {
    return styles.statusReady;
  }
  return styles.statusWatch;
}

function productEvidenceHref(productKind: StockProductKind) {
  if (productKind === "fund_or_etf") {
    return "#stock-fund-analysis";
  }
  return "#stock-financial-model";
}

function productEvidenceTitle(productKind: StockProductKind) {
  if (productKind === "fund_or_etf") {
    return "ETF·펀드 분석";
  }
  return "기업 분석";
}

function productEvidenceValue(productKind: StockProductKind, counts: StockHeaderCounts) {
  if (productKind === "fund_or_etf") {
    return counts.fundHoldingCount === null ? "구성 데이터 대기" : `${counts.fundHoldingCount.toLocaleString("ko-KR")}개 구성종목`;
  }
  return counts.financialMetricCount > 0 ? `${counts.financialMetricCount.toLocaleString("ko-KR")}개 재무 지표` : "재무 근거 대기";
}

function productEvidenceContext(productKind: StockProductKind) {
  if (productKind === "fund_or_etf") {
    return "구성종목, 비용률, NAV 괴리, 추적 품질이 판단의 중심이다.";
  }
  return "사업, 재무, 밸류에이션, 산업 위치가 판단의 중심이다.";
}

export function StockResearchHeader({
  symbol,
  name,
  marketCode,
  asOfDate,
  productKind,
  sourceBlocked,
  linkedThesisHref,
  viewModel,
  price,
  position,
  recommendation,
  counts,
}: StockResearchHeaderProps) {
  const productLabel = productKind === "fund_or_etf" ? "ETF·펀드" : "개별 회사";
  const recommendationHref = recommendation.href ?? "/recommendations";
  const recommendationCardClass = recommendation.href ? styles.mapCardReady : styles.mapCardWatch;
  const thesisCardClass = linkedThesisHref ? styles.mapCardReady : styles.mapCardBlocked;

  return (
    <section className={styles.header} aria-labelledby="stock-detail-title">
      <div className={styles.narrative}>
        <span className={styles.eyebrow}>
          종목 리서치 · {productLabel} · {marketCode} · {asOfDate}
        </span>
        <h1 className={styles.title} id="stock-detail-title">
          {symbol} 종목 분석서
        </h1>
        <p className={styles.summary}>
          {name}. {viewModel.investmentImpact}
        </p>
        <div className={styles.statusLine} aria-label={`${symbol} 핵심 상태`}>
          <span className={statusClassName(sourceBlocked, recommendation.href !== null)}>{viewModel.statusLabel}</span>
          <span className={styles.status}>{productLabel}</span>
          <span className={styles.status}>{position.statusLabel}</span>
          <span className={styles.status}>{price.priceSourceLabel}</span>
        </div>
        <div className={styles.metricGrid} aria-label={`${symbol} 핵심 지표`}>
          <article className={styles.metric}>
            <span>현재 가격</span>
            <strong>{price.priceLabel}</strong>
            <small>{price.priceSourceLabel}</small>
          </article>
          <article className={styles.metric}>
            <span>전일 대비</span>
            <SignedReturnBadge value={price.changePct} />
          </article>
          <article className={styles.metric}>
            <span>보유·평단</span>
            <strong>{position.averageCostLabel}</strong>
            <small>
              {position.quantityLabel} · {position.unrealizedPnlLabel}
            </small>
          </article>
          <article className={styles.metric}>
            <span>추천 상태</span>
            <strong>{recommendation.label}</strong>
            <small>{recommendation.context}</small>
          </article>
        </div>
      </div>

      <nav className={styles.map} aria-label={`${symbol} 종목 상세 읽는 순서`}>
        <h2 className={styles.mapTitle}>이 종목에서 먼저 볼 것</h2>
        <Link className={recommendationCardClass} href={recommendationHref}>
          <span>1. 추천 연결</span>
          <strong>{recommendation.label}</strong>
          <small>{recommendation.context}</small>
        </Link>
        <Link className={position.statusLabel === "보유 중" ? styles.mapCardReady : styles.mapCardWatch} href="/portfolio/coverage">
          <span>2. 보유 현실</span>
          <strong>{position.statusLabel}</strong>
          <small>
            {position.quantityLabel} · 평단 {position.averageCostLabel}
          </small>
        </Link>
        <a className={styles.mapCardPrimary} href="#stock-price-data">
          <span>3. 가격 출처</span>
          <strong>{price.priceLabel}</strong>
          <small>분석 기준 가격과 토스증권 브로커 데이터를 역할별로 분리한다.</small>
        </a>
        <a className={productKind === "fund_or_etf" ? styles.mapCardReady : styles.mapCard} href={productEvidenceHref(productKind)}>
          <span>4. {productEvidenceTitle(productKind)}</span>
          <strong>{productEvidenceValue(productKind, counts)}</strong>
          <small>{productEvidenceContext(productKind)}</small>
        </a>
        <a className={counts.stockNewsCount > 0 ? styles.mapCardReady : styles.mapCardWatch} href={counts.stockNewsCount > 0 ? "#stock-flow-impacts" : "/intelligence"}>
          <span>5. 뉴스·사이클</span>
          <strong>{counts.stockNewsCount.toLocaleString("ko-KR")}개 연결</strong>
          <small>
            직접 뉴스 {counts.directNewsCount.toLocaleString("ko-KR")}개 · 상위 흐름 {counts.macroFlowCount.toLocaleString("ko-KR")}개
          </small>
        </a>
        <a className={counts.marketCorrelationCount > 0 ? styles.mapCardReady : styles.mapCardWatch} href="#stock-market-correlations">
          <span>6. 시장 민감도</span>
          <strong>{counts.marketCorrelationCount.toLocaleString("ko-KR")}개 비교</strong>
          <small>지수, 금리, 달러, 원자재와 함께 움직인 정도를 보여준다.</small>
        </a>
        <Link className={thesisCardClass} href={linkedThesisHref ?? "/portfolio/coverage"}>
          <span>7. 투자 논리</span>
          <strong>{linkedThesisHref ? "연결됨" : "없음"}</strong>
          <small>{linkedThesisHref ? "매수 이유, 유지 조건, 무효화 조건으로 이어진다." : "중장기 판단 전 thesis 연결이 필요하다."}</small>
        </Link>
      </nav>
    </section>
  );
}
