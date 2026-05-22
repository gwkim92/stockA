import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { getAiEvidenceNeighborhood, getStockDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData, StockPrice } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "종목 상세" };

type StockDetailPageProps = {
  params: Promise<{ symbol: string }>;
};

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

function formatNumber(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "없음";
  }
  return value.toLocaleString("ko-KR");
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function formatCost(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "비용 없음";
  }
  return `$${value.toFixed(4)}`;
}

function formatStoryBasis(basis: string[]) {
  const labels: Record<string, string> = {
    same_title_signature: "제목 핵심 단어",
    same_source_document: "원천 문서 연결",
    same_theme: "테마 연결",
  };
  if (basis.length === 0) {
    return "단일 이벤트";
  }
  return basis.map((item) => labels[item] ?? koCode(item)).join(" · ");
}

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "날짜 없음";
}

function evidenceChunkPreview(value: string | null | undefined) {
  if (!value) {
    return "문서 미리보기 없음";
  }
  const titleMatch = value.match(/Title:\s*(.*?)(?:\s+Summary:|\s+Published\/Event At:|$)/);
  if (titleMatch?.[1]) {
    return `원문 제목: ${koLabel(titleMatch[1])}`;
  }
  return koLabel(value.split(" Retrieval context:")[0] ?? value);
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

function PriceChart({ bars, currencyCode }: { bars: StockPrice[]; currencyCode: string }) {
  const plotted = bars.filter((bar) => typeof bar.adjusted_close === "number" && bar.adjusted_close !== null);
  if (plotted.length < 2) {
    return <div className="empty-state">차트를 그릴 만큼 가격 데이터가 아직 충분하지 않다.</div>;
  }

  const closes = plotted.map((bar) => bar.adjusted_close as number);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const points = plotted
    .map((bar, index) => {
      const x = 40 + (index / Math.max(plotted.length - 1, 1)) * 780;
      const y = 186 - (((bar.adjusted_close as number) - min) / range) * 142;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const first = plotted[0];
  const last = plotted[plotted.length - 1];

  return (
    <figure className="price-chart" aria-label="종가 차트">
      <svg viewBox="0 0 860 240" role="img" aria-labelledby="price-chart-title">
        <title id="price-chart-title">수집된 조정 종가 흐름</title>
        <line x1="40" x2="820" y1="44" y2="44" />
        <line x1="40" x2="820" y1="115" y2="115" />
        <line x1="40" x2="820" y1="186" y2="186" />
        <polyline points={points} />
        <circle cx="40" cy={186 - (((first.adjusted_close as number) - min) / range) * 142} r="4" />
        <circle cx="820" cy={186 - (((last.adjusted_close as number) - min) / range) * 142} r="5" />
        <text x="40" y="222">{first.trade_date}</text>
        <text x="820" y="222" textAnchor="end">{last.trade_date}</text>
        <text x="40" y="30">{formatCurrency(max, currencyCode)}</text>
        <text x="820" y="205" textAnchor="end">{formatCurrency(min, currencyCode)}</text>
      </svg>
      <figcaption>
        최근 {plotted.length.toLocaleString("ko-KR")}개 거래일 조정 종가 기준. 투자 판단용 확정 신호가 아니라
        수집된 가격 데이터의 상태를 보여준다.
      </figcaption>
    </figure>
  );
}

function EvidenceNeighborhoodPanel({ neighborhood }: { neighborhood: AiEvidenceNeighborhoodData }) {
  const firstTheme = neighborhood.themes[0];
  const firstArtifact = neighborhood.ai_artifacts[0];
  const firstThesis = neighborhood.theses[0];
  const firstRecommendation = neighborhood.recommendations[0];
  const storyGroups = neighborhood.story_groups ?? [];

  return (
    <section className="bento-grid reveal delay-4" aria-label="이 종목이 뉴스와 엮인 이유">
      <article className="bento-card span-4" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
        <div className="section-heading">
          <div>
            <span className="metric-sub">뉴스와 종목 연결 이유</span>
            <h2>이 종목이 어떤 뉴스·테마 때문에 움직일 수 있는지 본다</h2>
          </div>
          <span className="bento-badge" style={{ margin: 0 }}>
            저장된 근거만 읽음 · 실시간 AI 호출 없음
          </span>
        </div>

        <div className="status-rail compact-rail" aria-label="뉴스와 종목 연결 요약">
          <div className="rail-cell">
            <span>이벤트</span>
            <strong>{neighborhood.summary.event_count}</strong>
            <small>종목에 연결된 뉴스/공시</small>
          </div>
          <div className="rail-cell">
            <span>뉴스 묶음</span>
            <strong>{neighborhood.summary.story_group_count ?? storyGroups.length}</strong>
            <small>같은 이야기 후보</small>
          </div>
          <div className="rail-cell">
            <span>AI 근거</span>
            <strong>{neighborhood.summary.ai_artifact_count}</strong>
            <small>저장된 구조화 증거</small>
          </div>
          <div className="rail-cell">
            <span>근거 문서</span>
            <strong>{neighborhood.summary.evidence_chunk_count}</strong>
            <small>검색 준비 {neighborhood.summary.embedded_chunk_count}개</small>
          </div>
          <div className="rail-cell">
            <span>투자 연결</span>
            <strong>{neighborhood.summary.thesis_count + neighborhood.summary.recommendation_count}</strong>
            <small>논리/추천 연결 수</small>
          </div>
        </div>

        <div className="trace-chain" aria-label={`${neighborhood.symbol} AI 증거 관계 흐름`}>
          <div className="trace-node">
            <span>발생</span>
            <strong>이벤트 {neighborhood.summary.event_count}개</strong>
            <p>
              {neighborhood.events[0]
                ? koLabel(neighborhood.events[0].title)
                : "아직 이 종목에 연결된 이벤트가 없다."}
            </p>
            <div className="mini-link-stack">
              <Link href={`/events?symbol=${encodeURIComponent(neighborhood.symbol)}` as Route}>이벤트 원장</Link>
            </div>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node">
            <span>테마</span>
            <strong>{firstTheme ? koCode(firstTheme.theme_key) : "테마 없음"}</strong>
            <p>
              {firstTheme
                ? `멤버십 ${koCode(firstTheme.membership_type)} · 신뢰도 ${formatPercent(firstTheme.confidence)}`
                : "테마 연결이 쌓이면 이 위치에 표시된다."}
            </p>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node">
            <span>AI 근거</span>
            <strong>{firstArtifact ? koCode(firstArtifact.evidence_type) : "AI 근거 없음"}</strong>
            <p>
              {firstArtifact
                ? `${koCode(firstArtifact.provider)} · 신뢰도 ${formatPercent(firstArtifact.confidence)} · 비용 ${formatCost(firstArtifact.estimated_cost_usd)}`
                : "아직 저장된 AI 구조화 증거가 없다."}
            </p>
            <div className="mini-link-stack">
              {firstArtifact ? <Link href={evidenceHref(firstArtifact.evidence_id) as Route}>AI 근거 열기</Link> : <span>근거 대기</span>}
            </div>
          </div>

          <div className="trace-arrow" aria-hidden="true">→</div>

          <div className="trace-node trace-node-final">
            <span>판단</span>
            <strong>{firstRecommendation ? koCode(firstRecommendation.action) : firstThesis ? "투자 논리만 있음" : "판단 대기"}</strong>
            <p>
              {firstRecommendation
                ? `점수 ${formatPercent(firstRecommendation.total_score)} · 목표 비중 ${formatPercent(firstRecommendation.recommended_weight)}`
                : firstThesis
                  ? `${koLabel(firstThesis.title)} · 확신 ${formatPercent(firstThesis.conviction_score)}`
                  : "추천이나 보유 판단으로 연결되기 전 단계다."}
            </p>
            <div className="mini-link-stack">
              {firstRecommendation ? <Link href={recommendationHref(firstRecommendation.recommendation_id)}>추천 검토서</Link> : null}
              {firstThesis ? <Link href={thesisHref(firstThesis.thesis_id)}>투자 논리</Link> : null}
            </div>
          </div>
        </div>

        <div className="relationship-panel" aria-label={`${neighborhood.symbol} 뉴스 이야기 묶음`}>
          <span>같은 이야기로 묶인 뉴스와 이유</span>
          <div className="relationship-list">
            {storyGroups.slice(0, 4).map((group) => {
              const firstSource = sourceDocumentHref(group.source_document_ids[0] ?? null);
              return (
                <div className="relationship-chip" key={group.story_id}>
                  <span>{formatStoryBasis(group.basis)}</span>
                  <NewsTitleBlock compact title={group.title} themeKey={group.theme_keys[0]} />
                  <small>
                    이벤트 {group.event_count.toLocaleString("ko-KR")}개 · 원천 {group.source_document_count.toLocaleString("ko-KR")}개 ·
                    문서 검색 청크 {group.linked_chunk_count.toLocaleString("ko-KR")}개 · 규칙 기반 신뢰도 {formatPercent(group.confidence)}
                  </small>
                  {group.relation_reasons.slice(0, 3).map((reason) => (
                    <small key={`${group.story_id}-${reason}`}>묶인 이유: {koLabel(reason)}</small>
                  ))}
                  {group.events.slice(0, 2).map((event) => (
                    <div className="nested-news-title" key={`${group.story_id}-${event.event_id}`}>
                      <small>대표 이벤트: {formatDate(event.event_at)} · {koCode(event.impact_direction)}</small>
                      <NewsTitleBlock
                        compact
                        title={event.title}
                        themeKey={event.theme_key}
                        impactDirection={event.impact_direction}
                        impactScore={event.impact_score}
                      />
                    </div>
                  ))}
                  <div className="mini-link-stack">
                    {firstSource ? <Link href={firstSource}>원천 문서</Link> : null}
                    <Link href={`/events?symbol=${encodeURIComponent(neighborhood.symbol)}` as Route}>이벤트 원장</Link>
                  </div>
                </div>
              );
            })}
            {storyGroups.length === 0 ? (
              <p className="relationship-empty">아직 같은 이야기로 묶을 수 있는 뉴스 근거가 없다.</p>
            ) : null}
          </div>
        </div>

        <div className="relationship-panel" aria-label={`${neighborhood.symbol} 저장된 증거 문서`}>
          <span>근거 문서 상태</span>
          <div className="relationship-list">
            {neighborhood.evidence_chunks.slice(0, 4).map((chunk) => {
              const document = sourceDocumentHref(chunk.source_document_id);
              const sourceKind =
                chunk.source_text_kind === "raw_html_text"
                  ? "원문 본문 추출"
                  : chunk.used_metadata_fallback
                    ? "본문 부족, 문서 정보 대체"
                    : "추출 상태 미확인";
              return (
                <div className="relationship-chip" key={chunk.chunk_id}>
                  <span>{chunk.used_metadata_fallback ? "요약 정보" : "원문 근거"}</span>
                  <strong>{evidenceChunkPreview(chunk.text_preview)}</strong>
                  <small>
                    {chunk.source_url_host || "출처 없음"} · {sourceKind} · 검색 준비 상태 {koCode(chunk.embedding_status)}
                  </small>
                  {document ? <Link href={document}>원천 문서 열기</Link> : null}
                </div>
              );
            })}
            {neighborhood.evidence_chunks.length === 0 ? (
              <p className="relationship-empty">아직 근거 검색에 사용할 문서 조각이 없다.</p>
            ) : null}
          </div>
        </div>

        <ul style={{ margin: "18px 0 0", paddingLeft: "20px", color: "var(--text-secondary)", lineHeight: 1.6 }}>
          {neighborhood.guardrails.map((guardrail) => (
            <li key={guardrail}>{koLabel(guardrail)}</li>
          ))}
        </ul>
      </article>
    </section>
  );
}

export default async function StockDetailPage({ params }: StockDetailPageProps) {
  const { symbol } = await params;
  const [response, neighborhoodResponse] = await Promise.all([
    getStockDetail(symbol),
    getAiEvidenceNeighborhood(symbol),
  ]);
  const data = response.data;
  const neighborhood = neighborhoodResponse.data;
  const hasPriceData = data.summary.bar_count > 0 && data.latest_price.close !== null;
  const hasEvidenceOnlyData =
    !hasPriceData && (data.macro_flow_impacts.length > 0 || data.recent_events.length > 0);
  const stockReadingCards = [
    {
      label: "먼저 볼 것",
      title: hasPriceData ? "가격 데이터가 있는 종목" : "가격보다 뉴스 흐름 먼저",
      body: hasPriceData
        ? `최근 가격일 ${data.latest_price.trade_date || data.summary.last_trade_date || "확인 필요"} 기준으로 차트와 수익률을 볼 수 있다.`
        : "가격 캔들이 부족하므로 추천 판단보다 뉴스·테마 연결 상태를 먼저 본다.",
    },
    {
      label: "직접 뉴스",
      title: `${data.recent_events.length}개`,
      body:
        data.recent_events.length > 0
          ? "회사명이나 티커가 직접 잡힌 뉴스다. 종목 판단에 가장 직접적인 근거다."
          : "아직 이 종목을 직접 언급한 최근 뉴스가 없다.",
    },
    {
      label: "상위 흐름",
      title: `${data.macro_flow_impacts.length}개`,
      body:
        data.macro_flow_impacts.length > 0
          ? "금리, 에너지, AI, 정책 같은 시장 흐름이 이 종목 노출도에 따라 전파됐다."
          : "시장·테마 뉴스가 이 종목 점수로 전파된 기록은 아직 없다.",
    },
    {
      label: "최종 확인",
      title: data.recommendation ? koCode(data.recommendation.action) : data.position ? "보유 상태 확인" : "판단 대기",
      body: data.recommendation
        ? "추천 상세에서 점수 재료와 보유검토 연결을 확인한다."
        : data.position
          ? "추천은 없지만 포트폴리오 보유 상태가 있으므로 보유검토를 확인한다."
          : "추천이나 보유 판단으로 연결되기 전 단계다.",
    },
  ];

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="stock-detail-title">
        <div className="bento-badge">
          종목 상세 • {data.market_code} • {data.as_of_date}
        </div>
        <h1 id="stock-detail-title">
          {hasEvidenceOnlyData ? `${data.symbol} 시장 흐름과 수집 상태` : `${data.symbol} 데이터와 판단 근거`}
        </h1>
        <p>
          가격 차트, 추천 상태, 보유 상태, 직접 뉴스, 상위 흐름 전파를 함께 확인한다.
          주문 판단보다 먼저 근거가 충분한지 확인하는 화면이다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="종목 요약">
        <div className="rail-cell">
          <span>최신 종가</span>
          <strong>{hasPriceData ? formatCurrency(data.latest_price.close, data.currency_code) : "가격 미수집"}</strong>
          <small>{data.latest_price.trade_date || "가격일 없음"}</small>
        </div>
        <div className="rail-cell">
          <span>수집 기간 수익률</span>
          <strong>{formatPercent(data.summary.return_pct)}</strong>
          <small>{data.summary.first_trade_date || "시작일 없음"}부터</small>
        </div>
        <div className="rail-cell">
          <span>추천 상태</span>
          <strong>{data.recommendation ? koCode(data.recommendation.action) : "추천 없음"}</strong>
          <small>{data.recommendation?.as_of_date || "추천 생성 전"}</small>
        </div>
        <div className="rail-cell">
          <span>보유 비중</span>
          <strong>{data.position ? formatPercent(data.position.weight) : "미보유"}</strong>
          <small>{data.position?.snapshot_date || "스냅샷 없음"}</small>
        </div>
      </section>

      <section className="detail-path-grid reveal delay-1" aria-label="종목 상세 읽는 순서">
        {stockReadingCards.map((card) => (
          <article className="detail-path-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.title}</strong>
            <p>{card.body}</p>
          </article>
        ))}
      </section>

      {hasEvidenceOnlyData ? (
        <section className="bento-card reveal delay-1" aria-label="가격 미수집 안내">
          <div className="section-heading stacked-heading">
            <span className="metric-sub">데이터 상태 구분</span>
            <h2>가격 데이터가 부족해 시장 흐름 노출부터 보여준다</h2>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: 0 }}>
            {data.symbol}은 현재 뉴스·테마 흐름에는 연결되어 있지만, 이 서버의 가격 캔들 수집 대상에는 아직 충분히
            포함되지 않았다. 따라서 가격 차트와 수익률은 판단하지 않고, 아래 상위 흐름/원천 뉴스만 검토한다.
          </p>
        </section>
      ) : null}

      <section className="bento-grid reveal delay-2">
        <article className="bento-card span-3">
          <div className="section-heading">
            <div>
              <span className="metric-sub">수집된 가격 차트</span>
              <h2>가격 흐름</h2>
            </div>
            <Link className="btn btn-secondary" href="/data-health">
              수집 상태 보기
            </Link>
          </div>
          <PriceChart bars={data.price_bars} currencyCode={data.currency_code} />
        </article>

        <article className="bento-card">
          <span className="metric-label">가격 데이터</span>
          <strong className="metric-value">{data.summary.bar_count.toLocaleString("ko-KR")}</strong>
          <span className="metric-sub">수집된 거래일 수</span>
          <div className="stock-meta-grid">
            <span>저가 종가</span>
            <strong>{formatCurrency(data.summary.low_close, data.currency_code)}</strong>
            <span>고가 종가</span>
            <strong>{formatCurrency(data.summary.high_close, data.currency_code)}</strong>
            <span>거래량</span>
            <strong>{formatNumber(data.latest_price.volume)}</strong>
          </div>
        </article>
      </section>

      <section className="bento-grid reveal delay-3">
        <article className="bento-card span-2">
          <div className="section-heading">
            <div>
              <span className="metric-sub">최근 추천</span>
              <h2>투자 판단 상태</h2>
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
                <Link href={thesisHref(data.recommendation.linked_thesis_id)}>
                  투자 논리 열기
                </Link>
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
              <span className="metric-sub">포트폴리오</span>
              <h2>보유 상태</h2>
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
              <strong>{formatNumber(data.position.quantity)}</strong>
              <span>평가액</span>
              <strong>{formatCurrency(data.position.market_value, data.currency_code)}</strong>
              <span>평가 가격</span>
              <strong>{formatCurrency(data.position.market_price, data.currency_code)}</strong>
            </div>
          ) : (
            <div className="empty-state">현재 포트폴리오 스냅샷에는 보유 포지션이 없다.</div>
          )}
        </article>
      </section>

      <EvidenceNeighborhoodPanel neighborhood={neighborhood} />

      <section className="bento-card span-4 reveal delay-4">
        <div className="section-heading">
          <div>
            <span className="metric-sub">상위 흐름 전파</span>
            <h2>시장·테마 뉴스가 이 종목에 준 영향</h2>
          </div>
          <Link className="btn btn-secondary" href="/intelligence">
            흐름 분석 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          회사가 직접 언급되지 않은 뉴스라도 금리, 에너지, AI 반도체 같은 상위 흐름이면 노출도에 따라 이 종목으로 영향이 전파된다.
        </p>
        <div className="bento-list">
          {data.macro_flow_impacts.length > 0 ? (
            data.macro_flow_impacts.map((flow) => {
              const evidence = evidenceHref(flow.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(flow.source_document_id);
              return (
                <div className="bento-list-item" key={`${flow.event_id}-${flow.theme_key}`}>
                  <div>
                    <span className="metric-sub">
                      {formatDate(flow.event_at)} • {koCode(flow.theme_key)} • {koCode(flow.impact_direction)}
                    </span>
                    <NewsTitleBlock
                      title={flow.title}
                      symbol={data.symbol}
                      themeKey={flow.theme_key}
                      impactDirection={flow.impact_direction}
                      impactScore={flow.impact_score}
                    />
                    <span>
                      전파 강도 {formatPercent(flow.impact_score)} · 노출도 {formatPercent(flow.exposure_weight)} · 신뢰도 {formatPercent(flow.confidence)}
                    </span>
                    {flow.rationale ? <span className="flow-rationale">{koLabel(flow.rationale)}</span> : null}
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    <Link className="btn btn-secondary" href={`/themes/${encodeURIComponent(flow.theme_key)}?asOfDate=${encodeURIComponent(data.as_of_date)}` as Route}>
                      흐름 보기
                    </Link>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>AI 증거</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>원천 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              아직 이 종목으로 전파된 상위 흐름이 없다. 직접 뉴스만 있거나 노출도 테이블에 연결되지 않은 상태다.
            </div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-4">
        <div className="section-heading">
          <div>
            <span className="metric-sub">직접 뉴스</span>
            <h2>이 종목이 직접 연결된 이벤트</h2>
          </div>
          <Link className="btn btn-secondary" href={`/events?symbol=${encodeURIComponent(data.symbol)}` as Route}>
            이벤트 화면
          </Link>
        </div>
        <div className="bento-list">
          {data.recent_events.length > 0 ? (
            data.recent_events.map((event) => {
              const evidence = evidenceHref(event.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(event.source_document_id);
              return (
                <div className="bento-list-item" key={event.event_id}>
                  <div>
                    <span className="metric-sub">{formatDate(event.event_at)} • {koCode(event.event_type)}</span>
                    <NewsTitleBlock
                      title={event.title}
                      symbol={data.symbol}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                    <span>{koCode(event.impact_direction)} • 영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>AI 증거</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>원천 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">아직 이 종목에 연결된 이벤트가 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
