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

type StockRow = Awaited<ReturnType<typeof getStocks>>["data"]["stocks"][number];

function stockPriorityReason(stock: StockRow) {
  if (stock.recommendation && stock.position) {
    return "추천 판단과 실제 보유가 모두 연결된 종목이다. 추천 이유와 현재 보유 상태가 서로 맞는지 먼저 본다.";
  }
  if (stock.recommendation) {
    return "추천 판단이 붙은 종목이다. 상세에서 뉴스, 사이클, 재무, 가격 근거가 충분한지 확인한다.";
  }
  if (stock.position) {
    return "보유 중인 종목이다. 상세에서 상위 흐름, 투자 논리, 가상 매매 검증 상태를 확인한다.";
  }
  return "가격 데이터가 수집된 종목이다. 추천 전 단계의 관찰 대상으로 본다.";
}

function formatSymbolList(stocks: StockRow[]) {
  if (stocks.length === 0) {
    return "해당 없음";
  }
  return stocks
    .slice(0, 4)
    .map((stock) => stock.symbol)
    .join(" · ");
}

export default async function StocksPage() {
  const response = await getStocks();
  const data = response.data;
  const recommendedStocks = data.stocks.filter((stock) => stock.recommendation);
  const heldStocks = data.stocks.filter((stock) => stock.position);
  const watchOnlyStocks = data.stocks.filter((stock) => !stock.recommendation && !stock.position);
  const staleOrMissingPriceStocks = data.stocks.filter(
    (stock) => !stock.latest_price.trade_date || stock.latest_price.trade_date !== data.summary.latest_price_date,
  );
  const priorityStocks = data.stocks
    .slice()
    .sort((left, right) => {
      const leftScore = Number(Boolean(left.recommendation)) * 2 + Number(Boolean(left.position));
      const rightScore = Number(Boolean(right.recommendation)) * 2 + Number(Boolean(right.position));
      return rightScore - leftScore || left.symbol.localeCompare(right.symbol);
    })
    .slice(0, 3);
  const stockCommandCards = [
    {
      index: "01",
      label: "추천 연결",
      title:
        recommendedStocks.length > 0
          ? `${recommendedStocks.length.toLocaleString("ko-KR")}개 종목`
          : "추천 연결 없음",
      metric: formatSymbolList(recommendedStocks),
      body:
        recommendedStocks.length > 0
          ? "추천 판단이 붙은 종목이다. 상세에서 뉴스·사이클·재무·밸류에이션 근거가 같이 맞는지 본다."
          : "현재 목록에는 추천 판단이 붙은 종목이 없다. 추천 생성 상태를 먼저 확인한다.",
      href: "/recommendations",
      cta: "추천 근거 보기",
      tone: recommendedStocks.length > 0 ? "watch" : "block",
    },
    {
      index: "02",
      label: "보유 연결",
      title:
        heldStocks.length > 0
          ? `${heldStocks.length.toLocaleString("ko-KR")}개 보유`
          : "보유 연결 없음",
      metric: formatSymbolList(heldStocks),
      body:
        heldStocks.length > 0
          ? "포트폴리오에 연결된 종목이다. 추천 방향과 현재 보유 비중이 충돌하지 않는지 보유 검토에서 확인한다."
          : "현재 포트폴리오 스냅샷에 연결된 보유 종목이 없다.",
      href: "/portfolio/coverage",
      cta: "보유 검토 보기",
      tone: heldStocks.length > 0 ? "ready" : "watch",
    },
    {
      index: "03",
      label: "관찰 종목",
      title:
        watchOnlyStocks.length > 0
          ? `${watchOnlyStocks.length.toLocaleString("ko-KR")}개 관찰`
          : "관찰 전용 없음",
      metric: formatSymbolList(watchOnlyStocks),
      body:
        watchOnlyStocks.length > 0
          ? "가격은 수집됐지만 추천이나 보유가 아직 붙지 않은 종목이다. 상세에서 차트와 상위 흐름을 먼저 확인한다."
          : "모든 종목이 추천이나 보유 상태와 연결돼 있다.",
      href: "#stock-list",
      cta: "목록에서 찾기",
      tone: watchOnlyStocks.length > 0 ? "watch" : "ready",
    },
    {
      index: "04",
      label: "데이터 점검",
      title:
        staleOrMissingPriceStocks.length > 0
          ? "가격 갱신 확인"
          : "가격일 일치",
      metric: `${staleOrMissingPriceStocks.length.toLocaleString("ko-KR")}개 확인 · 최신 ${data.summary.latest_price_date || "없음"}`,
      body:
        staleOrMissingPriceStocks.length > 0
          ? "최신 가격일과 다른 종목이 있다. 투자 판단 전에 수집 상태와 종목 상세의 데이터 기간을 확인한다."
          : "목록의 가격 관측일이 최신 기준일과 맞는다. 그래도 재무·공시 근거 부족 여부는 종목 상세에서 본다.",
      href: "/data-health",
      cta: "수집 상태 보기",
      tone: staleOrMissingPriceStocks.length > 0 ? "block" : "ready",
    },
  ];

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="stocks-title">
        <div className="bento-badge">종목 지도 • 추천·보유·관찰 분류</div>
        <h1 id="stocks-title">오늘 볼 종목을 고르고 상세 근거로 들어간다.</h1>
        <p>
          추천이 붙은 종목, 실제 보유와 연결된 종목, 아직 관찰 단계인 종목을 나눠 본다.
          이 목록은 주문 화면이 아니며, 재무·공시 근거와 AI 해석은 종목 상세에서 확인한다.
        </p>
      </section>

      <section className="stocks-command-panel reveal delay-1" aria-labelledby="stocks-command-title">
        <div className="stocks-command-lead">
          <span>종목 우선순위</span>
          <h2 id="stocks-command-title">추천, 보유, 관찰, 데이터 점검으로 먼저 볼 순서를 정한다.</h2>
          <p>
            총 {data.stock_count.toLocaleString("ko-KR")}개 · 가격 수집 {data.summary.priced_stock_count.toLocaleString("ko-KR")}개 ·
            최신 가격일 {data.summary.latest_price_date || "없음"}. 재무·공시 근거, 기업 분석, 가상 매매 검증 상태는 각 종목 상세에서 확인한다.
          </p>
        </div>
        <div className="stocks-command-grid">
          {stockCommandCards.map((card) => (
            <a className={`stocks-command-card ${card.tone}`} href={card.href} key={card.index}>
              <span>{card.index}</span>
              <small>{card.label}</small>
              <strong>{card.title}</strong>
              <em>{card.metric}</em>
              <p>{card.body}</p>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="feature-map-panel reveal delay-2" aria-labelledby="stock-priority-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">오늘 먼저 볼 종목</span>
            <h2 id="stock-priority-title">판단이 이미 걸린 종목부터 연다</h2>
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

      <section className="bento-card span-4 reveal delay-3" id="stock-list" aria-labelledby="stock-list-title">
        <div className="section-heading">
          <div>
            <span className="metric-sub">종목 목록</span>
            <h2 id="stock-list-title">종목명과 버튼으로 필요한 화면만 연다</h2>
          </div>
          <Link className="btn btn-secondary" href="/data-health">
            데이터 수집 상태 보기
          </Link>
        </div>
        <p className="section-note">
          행 전체가 눌리는 구조가 아니다. 종목명이나 오른쪽의 <strong>종목 상세 보기</strong> 버튼을 눌러 이동한다.
          추천 판단이 붙은 종목은 <strong>추천 근거 보기</strong>로 바로 이어진다.
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
