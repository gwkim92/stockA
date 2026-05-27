import Link from "next/link";
import type { Route } from "next";

import { getStocks } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목" };

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${encodeURIComponent(recommendationId)}` as Route;
}

function stockPriorityReason(stock: Awaited<ReturnType<typeof getStocks>>["data"]["stocks"][number]) {
  if (stock.recommendation && stock.position) {
    return "추천과 보유가 모두 연결된 종목이다. 추천 논리와 현재 보유 상태가 충돌하지 않는지 먼저 본다.";
  }
  if (stock.recommendation) {
    return "추천 근거가 붙은 종목이다. 상세에서 뉴스·사이클·재무 근거가 충분한지 확인한다.";
  }
  if (stock.position) {
    return "보유 중인 종목이다. 상세에서 상위 흐름, thesis, 페이퍼 검증 상태를 확인한다.";
  }
  return "가격 데이터가 수집된 종목이다. 추천 전 단계의 관찰 대상으로 본다.";
}

export default async function StocksPage() {
  const response = await getStocks();
  const data = response.data;
  const priorityStocks = data.stocks
    .slice()
    .sort((left, right) => {
      const leftScore = Number(Boolean(left.recommendation)) * 2 + Number(Boolean(left.position));
      const rightScore = Number(Boolean(right.recommendation)) * 2 + Number(Boolean(right.position));
      return rightScore - leftScore || left.symbol.localeCompare(right.symbol);
    })
    .slice(0, 3);

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="stocks-title">
        <div className="bento-badge">종목 확인실 • 상세 분석 입구</div>
        <h1 id="stocks-title">종목을 고르고 상세 분석으로 들어간다.</h1>
        <p>
          이 화면은 DB에 들어온 종목을 나열하는 곳이다. 추천이 붙었는지, 보유 중인지, 가격 데이터가
          충분한지를 먼저 보고 오른쪽의 명확한 버튼으로 종목 상세나 추천 근거로 이동한다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="종목 데이터 요약">
        <div className="rail-cell">
          <span>수집 종목</span>
          <strong>{data.stock_count.toLocaleString("ko-KR")}</strong>
          <small>가격 데이터가 있는 종목</small>
        </div>
        <div className="rail-cell">
          <span>최신 가격일</span>
          <strong>{data.summary.latest_price_date || "없음"}</strong>
          <small>시장 데이터 최종 관측일</small>
        </div>
        <div className="rail-cell">
          <span>추천 연결</span>
          <strong>{data.summary.recommended_stock_count.toLocaleString("ko-KR")}</strong>
          <small>추천/논리가 붙은 종목</small>
        </div>
        <div className="rail-cell">
          <span>보유 중</span>
          <strong>{data.summary.held_stock_count.toLocaleString("ko-KR")}</strong>
          <small>포트폴리오 스냅샷 기준</small>
        </div>
      </section>

      <section className="feature-map-panel reveal delay-2" aria-labelledby="stock-priority-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">오늘 먼저 볼 종목</span>
            <h2 id="stock-priority-title">추천·보유 연결이 있는 종목부터 확인한다</h2>
          </div>
          <Link className="btn btn-secondary" href="/recommendations">
            추천 후보 전체 보기
          </Link>
        </div>
        <div className="insight-grid">
          {priorityStocks.map((stock) => (
            <article className="feature-map-card collection-map-card" key={`priority-${stock.symbol}`}>
              <span>{stock.recommendation ? "추천 연결" : stock.position ? "보유 종목" : "관찰 종목"}</span>
              <strong>{stock.symbol}</strong>
              <small>{stock.name}</small>
              <p>{stockPriorityReason(stock)}</p>
              <div className="btn-row decision-actions">
                <Link className="btn btn-primary" href={stockHref(stock.symbol)}>
                  종목 상세 보기
                </Link>
                {stock.recommendation ? (
                  <Link className="btn btn-secondary" href={recommendationHref(stock.recommendation.recommendation_id)}>
                    추천 근거 보기
                  </Link>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-3" aria-labelledby="stock-list-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">종목 목록</span>
            <h2 id="stock-list-title">종목별 상세로 바로 이동한다</h2>
          </div>
          <Link className="btn btn-secondary" href="/data-health">
            데이터 수집 상태 보기
          </Link>
        </div>
        <p className="section-note">
          행 전체는 링크가 아니다. 종목명이나 오른쪽의 <strong>종목 상세 보기</strong> 버튼을 눌러 이동한다.
          추천이 붙은 종목은 <strong>추천 근거 보기</strong>로 바로 이어진다.
        </p>

        <div className="stock-table" role="table" aria-label="수집된 종목 목록">
          <div className="stock-table-row stock-table-head" role="row">
            <span role="columnheader">종목</span>
            <span role="columnheader">최신 가격</span>
            <span role="columnheader">가격일</span>
            <span role="columnheader">수집 길이</span>
            <span role="columnheader">추천 상태</span>
            <span role="columnheader">보유 비중</span>
            <span role="columnheader">상세 확인</span>
          </div>
          {data.stocks.map((stock) => {
            const recommendationLink = stock.recommendation
              ? recommendationHref(stock.recommendation.recommendation_id)
              : null;

            return (
              <div className="stock-table-row" key={stock.symbol} role="row">
                <span role="cell">
                  <Link
                    aria-label={`${stock.symbol} 종목 상세 보기`}
                    className="stock-symbol-link"
                    href={stockHref(stock.symbol)}
                  >
                    <strong>{stock.symbol}</strong>
                    <small>{stock.name}</small>
                  </Link>
                </span>
                <span role="cell">
                  <strong>{formatCurrency(stock.latest_price.close, stock.currency_code)}</strong>
                  <small>{formatPercent(stock.latest_price.change_pct)}</small>
                </span>
                <span role="cell">{stock.latest_price.trade_date || "없음"}</span>
                <span role="cell">
                  {stock.data_coverage.bar_count.toLocaleString("ko-KR")}일
                  <small>{stock.data_coverage.first_trade_date || "시작일 없음"}</small>
                </span>
                <span role="cell">
                  {stock.recommendation ? koCode(stock.recommendation.action) : "추천 없음"}
                  <small>
                    {stock.recommendation
                      ? `${stock.recommendation.as_of_date} · 점수 ${formatPercent(stock.recommendation.score)}`
                      : "검토 전"}
                  </small>
                </span>
                <span role="cell">
                  {stock.position ? formatPercent(stock.position.weight) : "미보유"}
                  <small>{stock.position ? koLabel(stock.position.portfolio_name) : "포트폴리오 없음"}</small>
                </span>
                <span className="stock-action-cell" role="cell">
                  <Link className="btn btn-primary" href={stockHref(stock.symbol)}>
                    종목 상세 보기
                  </Link>
                  {recommendationLink ? (
                    <Link className="btn btn-secondary" href={recommendationLink}>
                      추천 근거 보기
                    </Link>
                  ) : null}
                </span>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
