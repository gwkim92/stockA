import Link from "next/link";
import type { Route } from "next";

import { koCode, koLabel } from "@/lib/korean-labels";
import type { StockDetailData } from "@/lib/types";

import { formatCurrency, formatPercent } from "./stock-detail-panel-format";

type StockRecommendationPositionPanelProps = {
  readonly data: StockDetailData;
  readonly portfolioQuantity: number | null;
  readonly portfolioAverageCost: number | null;
  readonly portfolioMarketValue: number | null;
  readonly portfolioUnrealizedPnl: number | null;
  readonly portfolioUnrealizedPnlPct: number | null;
};

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return value.toLocaleString("ko-KR");
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

export function StockRecommendationPositionPanel({
  data,
  portfolioQuantity,
  portfolioAverageCost,
  portfolioMarketValue,
  portfolioUnrealizedPnl,
  portfolioUnrealizedPnlPct,
}: StockRecommendationPositionPanelProps) {
  return (
    <section className="bento-grid reveal delay-3" id="stock-recommendation-status" aria-label="추천과 보유 상태">
      <article className="bento-card span-2">
        <div className="section-heading">
          <div>
            <span className="metric-sub">추천 판단</span>
            <h2>추천 근거와 거래 경계</h2>
          </div>
          {data.recommendation ? (
            <Link className="btn btn-primary" href={recommendationHref(data.recommendation.recommendation_id)}>
              추천 상세
            </Link>
          ) : null}
        </div>
        {data.recommendation ? (
          <div className="stock-meta-grid">
            <span>판단</span>
            <strong>{koCode(data.recommendation.action)}</strong>
            <span>점수</span>
            <strong>{formatPercent(data.recommendation.score)}</strong>
            <span>상태</span>
            <strong>{koCode(data.recommendation.status)}</strong>
            <span>투자 논리</span>
            {data.recommendation.linked_thesis_id ? (
              <Link href={thesisHref(data.recommendation.linked_thesis_id)}>투자 논리 열기</Link>
            ) : (
              <strong>없음</strong>
            )}
          </div>
        ) : (
          <div className="empty-state">이 종목은 아직 추천 점수와 투자 논리가 붙지 않았다.</div>
        )}
      </article>

      <article className="bento-card span-2">
        <div className="section-heading">
          <div>
            <span className="metric-sub">보유 상태</span>
            <h2>보유 포지션과 평가손익</h2>
          </div>
          <Link className="btn btn-secondary" href="/portfolio/coverage">
            포트폴리오 보기
          </Link>
        </div>
        {data.position ? (
          <div className="stock-meta-grid">
            <span>포트폴리오</span>
            <strong>{koLabel(data.position.portfolio_name)}</strong>
            <span>수량</span>
            <strong>{formatNumber(portfolioQuantity)}</strong>
            <span>평단가</span>
            <strong>{portfolioAverageCost !== null ? formatCurrency(portfolioAverageCost, data.currency_code) : "평단 자료 없음"}</strong>
            <span>평가액</span>
            <strong>{formatCurrency(portfolioMarketValue, data.currency_code)}</strong>
            <span>평가 가격</span>
            <strong>{formatCurrency(data.position.market_price, data.currency_code)}</strong>
            <span>평가손익</span>
            <strong>
              {portfolioUnrealizedPnl !== null
                ? `${formatCurrency(portfolioUnrealizedPnl, data.currency_code)} · ${formatPercent(portfolioUnrealizedPnlPct)}`
                : "평가손익 자료 없음"}
            </strong>
          </div>
        ) : (
          <div className="empty-state">현재 포트폴리오 스냅샷에는 보유 포지션이 없다.</div>
        )}
      </article>
    </section>
  );
}

