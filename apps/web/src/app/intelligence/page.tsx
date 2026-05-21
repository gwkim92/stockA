import Link from "next/link";
import type { Route } from "next";

import {
  getAiNewsClusters,
  getCycleStates,
  getDataHealth,
  getEvents,
  getPaperTradingPreview,
  getPortfolioCoverage,
  getThemeDetail,
} from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { AiNewsClusterListData, DataHealthData, EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "분석 지도" };

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function maybeRoute(path: string | null | undefined) {
  return path ? (path as Route) : null;
}

function aiEvidenceLabel(type: string | null) {
  if (type === "news_event_candidate") {
    return "뉴스 AI 후보";
  }
  if (type === "news_cluster_summary") {
    return "뉴스 묶음 증거";
  }
  if (type) {
    return koCode(type);
  }
  return "AI 분석 대기";
}

type NewsEvent = EventListData["events"][number];
type StoredAiNewsCluster = AiNewsClusterListData["clusters"][number];
type PipelineRun = DataHealthData["pipeline_runs"][number];

type NewsCluster = {
  key: string;
  themeKey: string;
  themeName: string;
  eventCount: number;
  latestAt: string;
  symbols: string[];
  sourceDocumentCount: number;
  supportiveCount: number;
  riskReviewCount: number;
  watchCount: number;
  relationTypes: string[];
  examples: NewsEvent[];
};

function isKnownCode(value: string | null | undefined) {
  if (!value) {
    return false;
  }
  return value !== "UNKNOWN" && value !== "UNCLASSIFIED";
}

function buildNewsClusters(events: NewsEvent[]) {
  const clusters = new Map<
    string,
    NewsCluster & {
      symbolSet: Set<string>;
      sourceDocumentSet: Set<string>;
      relationTypeSet: Set<string>;
    }
  >();

  for (const event of events) {
    const key = event.theme_key || "UNCLASSIFIED";
    const current =
      clusters.get(key) ??
      {
        key,
        themeKey: event.theme_key,
        themeName: event.theme_name,
        eventCount: 0,
        latestAt: event.event_at,
        symbols: [],
        sourceDocumentCount: 0,
        supportiveCount: 0,
        riskReviewCount: 0,
        watchCount: 0,
        relationTypes: [],
        examples: [],
        symbolSet: new Set<string>(),
        sourceDocumentSet: new Set<string>(),
        relationTypeSet: new Set<string>(),
      };

    current.eventCount += 1;
    current.latestAt = event.event_at > current.latestAt ? event.event_at : current.latestAt;
    if (isKnownCode(event.symbol)) {
      current.symbolSet.add(event.symbol);
    }
    if (event.source_document_id) {
      current.sourceDocumentSet.add(event.source_document_id);
    }
    if (event.impact_direction === "supportive") {
      current.supportiveCount += 1;
    } else if (event.impact_direction === "risk_review") {
      current.riskReviewCount += 1;
    } else {
      current.watchCount += 1;
    }
    for (const related of event.related_events) {
      current.relationTypeSet.add(related.relation_type);
      if (isKnownCode(related.symbol)) {
        current.symbolSet.add(related.symbol);
      }
    }
    if (current.examples.length < 3) {
      current.examples.push(event);
    }

    clusters.set(key, current);
  }

  return Array.from(clusters.values())
    .map((cluster) => ({
      ...cluster,
      symbols: Array.from(cluster.symbolSet).sort(),
      sourceDocumentCount: cluster.sourceDocumentSet.size,
      relationTypes: Array.from(cluster.relationTypeSet).sort(),
    }))
    .sort((left, right) => {
      if (right.eventCount !== left.eventCount) {
        return right.eventCount - left.eventCount;
      }
      return right.latestAt.localeCompare(left.latestAt);
    })
    .slice(0, 4);
}

function formatSymbols(symbols: string[]) {
  if (symbols.length === 0) {
    return "연결 종목 대기";
  }
  return symbols.slice(0, 5).map(koCode).join(", ");
}

function formatClusterTone(cluster: NewsCluster) {
  const parts = [
    cluster.supportiveCount > 0 ? `우호 ${cluster.supportiveCount}` : null,
    cluster.riskReviewCount > 0 ? `리스크 ${cluster.riskReviewCount}` : null,
    cluster.watchCount > 0 ? `관찰 ${cluster.watchCount}` : null,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "영향 미분류";
}

function formatRelationTypes(relationTypes: string[]) {
  if (relationTypes.length === 0) {
    return "같은 테마/종목 관계가 더 쌓이면 자동으로 표시";
  }
  return relationTypes.map(koCode).join(" · ");
}

function formatDirectionCounts(counts: Record<string, number>) {
  const entries = Object.entries(counts).filter(([, count]) => count > 0);
  if (entries.length === 0) {
    return "방향성 미분류";
  }
  return entries.map(([key, count]) => `${koCode(key)} ${count}`).join(" · ");
}

function formatClusterRagStatus(cluster: StoredAiNewsCluster) {
  if (cluster.chunk_count === 0) {
    return "검색 준비 전";
  }
  if (cluster.embedded_chunk_count === cluster.chunk_count) {
    return "검색 준비 완료";
  }
  return `부분 준비 ${cluster.embedded_chunk_count}/${cluster.chunk_count}`;
}

function findNewsPipelineRun(dataHealth: DataHealthData): PipelineRun | null {
  return (
    dataHealth.pipeline_runs.find((run) => run.job_id === "news-rss-daily")
    ?? dataHealth.pipeline_runs.find((run) => run.pipeline_name === "news_rss_upsert")
    ?? null
  );
}

function formatNewsRunStatus(newsRun: PipelineRun | null) {
  if (!newsRun) {
    return "실행 이력 없음";
  }
  return `${koCode(newsRun.latest_status)} · ${koCode(newsRun.health_status)}`;
}

function newsRunLabel(newsRun: PipelineRun | null) {
  if (!newsRun) {
    return "뉴스 RSS 일일 수집";
  }
  if (newsRun.job_id === "news-rss-daily" || newsRun.pipeline_name === "news_rss_upsert") {
    return "뉴스 RSS 일일 수집";
  }
  return koCode(newsRun.job_id);
}

function latestFreshnessDate(dataHealth: DataHealthData, dataset: string) {
  return (
    dataHealth.freshness.find((item) => item.dataset === dataset)?.latest_observation_date ||
    "2024-11-01"
  );
}

export default async function IntelligencePage() {
  const dataHealthResponse = await getDataHealth();
  const dataHealth = dataHealthResponse.data;
  const portfolioCoverageDate = latestFreshnessDate(dataHealth, "portfolio.position_snapshot");
  const [
    eventsResponse,
    newsClusterResponse,
    cyclesResponse,
    themeResponse,
    portfolioResponse,
    paperResponse,
  ] = await Promise.all([
    getEvents(),
    getAiNewsClusters({ limit: 4 }),
    getCycleStates(),
    getThemeDetail("ANNUAL_REPORTING"),
    getPortfolioCoverage(portfolioCoverageDate),
    getPaperTradingPreview(),
  ]);

  const events = eventsResponse.data;
  const storedNewsClusters = newsClusterResponse.data;
  const cycles = cyclesResponse.data;
  const theme = themeResponse.data;
  const portfolio = portfolioResponse.data;
  const paper = paperResponse.data;
  const newsRun = findNewsPipelineRun(dataHealth);
  const schedulerActivation = dataHealth.scheduler.activation;

  const cycleByTheme = new Map(cycles.cycle_states.map((cycle) => [cycle.theme_key, cycle]));
  const positionBySymbol = new Map(portfolio.positions.map((position) => [position.symbol, position]));
  const paperActionBySymbol = new Map(paper.paper_actions.map((action) => [action.symbol, action]));
  const themeInstrumentBySymbol = new Map(theme.linked_instruments.map((instrument) => [instrument.symbol, instrument]));
  const firstEvent = events.events[0];
  const firstRecommendationId =
    theme.linked_instruments.find((instrument) => instrument.latest_recommendation_id)?.latest_recommendation_id ??
    paper.paper_actions.find((action) => action.recommendation_id)?.recommendation_id ??
    null;
  const firstThesisId =
    theme.linked_instruments.find((instrument) => instrument.active_thesis_id)?.active_thesis_id ??
    paper.paper_actions.find((action) => action.linked_thesis_id)?.linked_thesis_id ??
    null;
  const firstEvidenceId = firstEvent?.ai_evidence_id ?? null;
  const aiAttached = events.summary.ai_extracted_count > 0;
  const newsClusters = buildNewsClusters(events.events);
  const tracedEvents = events.events.slice(0, 5);
  const hiddenTraceCount = Math.max(0, events.events.length - tracedEvents.length);

  const locationCards = [
    {
      index: "01",
      title: "신호와 사이클",
      copy: "테마가 어느 국면에 있는지와 가격·이벤트 입력이 어떻게 변했는지 본다.",
      href: "/cycles",
      cta: "사이클 보드",
    },
    {
      index: "02",
      title: "추천",
      copy: "장기 후보, 점수 구성요소, 연결 근거, 아직 막힌 사유를 같이 본다.",
      href: firstRecommendationId ? `/recommendations/${firstRecommendationId}` : "/recommendations/AAPL-2024-11-01",
      cta: "추천 검토서",
    },
    {
      index: "03",
      title: "보유검토",
      copy: "보유 종목에 투자 논리와 성과 측정이 붙었는지 점검한다.",
      href: "/portfolio/coverage",
      cta: "보유 검토 지도",
    },
    {
      index: "04",
      title: "AI 분석 근거",
      copy: "개별 뉴스 후보 분석과 뉴스 묶음 증거의 원문, 신뢰도, 검증 상태를 본다.",
      href: firstEvidenceId ? `/ai-evidence/${firstEvidenceId}` : "/ai-evidence/ai-evidence-1",
      cta: "AI 근거",
    },
  ];

  return (
    <div className="terminal-page intelligence-page">
      <section className="page-hero reveal" aria-labelledby="intelligence-title">
        <div>
          <div className="bento-badge">분석 지도</div>
          <h1 className="page-title" id="intelligence-title">
            뉴스는 묶어서 보고, 중요한 뉴스만 AI 후보로 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          먼저 저장된 뉴스 묶음으로 시장 흐름을 보고, 다음에 개별 AI 후보의 원천과 신뢰도를 확인한다.
          마지막으로 종목, 추천, 보유 검토에 연결된 근거만 따라가면 된다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="분석 지도 요약">
        <article className="rail-cell">
          <span>01 이벤트</span>
          <strong>{events.summary.event_count}</strong>
          <small>공시/이벤트 원장</small>
        </article>
        <article className="rail-cell">
          <span>02 AI 분석</span>
          <strong>{events.summary.ai_extracted_count}</strong>
          <small>{aiAttached ? "원천 증거 연결됨" : "아직 연결 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>03 테마</span>
          <strong>{events.summary.themes_represented}</strong>
          <small>사이클 상태 {koCode(theme.state)}</small>
        </article>
        <article className="rail-cell">
          <span>04 보유 커버리지</span>
          <strong className="rail-ratio-value">{formatPercent(portfolio.summary.weight_coverage_ratio)}</strong>
          <small>투자 논리/성과 연결률</small>
        </article>
      </section>

      <section className="flow-panel reveal delay-2" aria-labelledby="news-operation-title">
        <div className="section-heading flow-heading">
          <span>읽는 순서</span>
          <h2 id="news-operation-title">이 화면에서 볼 것은 세 가지다</h2>
        </div>

        <section className="status-rail compact-rail" aria-label="뉴스 수집 자동화 상태">
          <article className="rail-cell">
            <span>수집 작업</span>
            <strong>{newsRunLabel(newsRun)}</strong>
            <small>{newsRun ? `${koCode(newsRun.cadence)} · ${newsRun.expected_after_local}` : "매일 08:30 기준"}</small>
          </article>
          <article className="rail-cell">
            <span>최근 상태</span>
            <strong>{formatNewsRunStatus(newsRun)}</strong>
            <small>{newsRun?.finished_at ?? "최근 완료 시각 없음"}</small>
          </article>
          <article className="rail-cell">
            <span>자동화 승인</span>
            <strong>{koCode(schedulerActivation.status)}</strong>
            <small>{schedulerActivation.activation_allowed ? "활성화 가능" : "수동/승인 대기"}</small>
          </article>
          <article className="rail-cell">
            <span>추천 반영</span>
            <strong>자동 주문 없음</strong>
            <small>증거·품질 관문으로만 사용</small>
          </article>
        </section>

        <div className="flow-steps" style={{ marginTop: "18px" }}>
          <article className="flow-step">
            <span>01</span>
            <strong>뉴스 묶음</strong>
            <p>
              같은 테마의 뉴스를 묶어 큰 흐름을 본다. 이것은 “무슨 일이 많이 발생했나”를 보는 영역이다.
            </p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>개별 AI 후보</strong>
            <p>
              중요한 뉴스는 AI가 종목, 테마, 영향 방향, 불확실성을 구조화한다. 원천 없는 해석은 검증에서 막는다.
            </p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>투자 입력</strong>
            <p>
              통과한 증거만 추천, 보유 검토, 가상 거래 안전 점검의 입력 후보가 된다. 자동 주문은 하지 않는다.
            </p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>자동화 상태</strong>
            <p>
              수집과 분석은 EC2의 timer가 실행하고, 실행 결과는 데이터 수집 화면과 파이프라인 이력에 남는다.
            </p>
          </article>
          <article className="flow-step">
            <span>05</span>
            <strong>상세 원장</strong>
            <p>
              전체 뉴스 목록은 이벤트 원장, 개별 AI 분석은 AI 후보 목록에서 본다. 이 화면은 대표 흐름만 보여준다.
            </p>
          </article>
        </div>
      </section>

      <section className="where-grid reveal delay-2" aria-label="신호 추천 보유검토 위치">
        {locationCards.map((card) => (
          <Link className="where-card" href={card.href as Route} key={card.index}>
            <span>{card.index}</span>
            <strong>{card.title}</strong>
            <p>{card.copy}</p>
            <small>{card.cta} 열기</small>
          </Link>
        ))}
      </section>

      <section className="intelligence-board reveal delay-2" aria-labelledby="stored-news-cluster-title">
        <div className="section-heading stacked-heading">
          <span>저장된 뉴스 증거</span>
          <h2 id="stored-news-cluster-title">뉴스 묶음은 흐름을, 개별 AI 후보는 영향 해석을 보여준다</h2>
        </div>

        <section className="status-rail compact-rail" aria-label="저장된 AI 뉴스 묶음 요약">
          <article className="rail-cell">
            <span>뉴스 묶음</span>
            <strong>{storedNewsClusters.summary.cluster_count}</strong>
            <small>같은 테마로 묶인 증거</small>
          </article>
          <article className="rail-cell">
            <span>묶인 뉴스</span>
            <strong>{storedNewsClusters.summary.clustered_event_count}</strong>
            <small>뉴스 묶음에 포함된 이벤트</small>
          </article>
          <article className="rail-cell">
            <span>검색 청크</span>
            <strong>{storedNewsClusters.summary.chunk_count}</strong>
            <small>임베딩 {storedNewsClusters.summary.embedded_chunk_count}개</small>
          </article>
          <article className="rail-cell">
            <span>묶음 비용</span>
            <strong>${storedNewsClusters.summary.estimated_cost_usd.toFixed(4)}</strong>
            <small>실시간 LLM 호출 없음</small>
          </article>
        </section>

        {storedNewsClusters.clusters.length > 0 ? (
          <div className="trace-grid" style={{ marginTop: "18px" }}>
            {storedNewsClusters.clusters.map((cluster) => {
              const evidenceHref = `/ai-evidence/${cluster.evidence_id}` as Route;
              const firstSource = cluster.source_documents[0];
              const firstSymbol = cluster.symbols[0];
              const stockHref = firstSymbol ? (`/stocks/${encodeURIComponent(firstSymbol)}` as Route) : null;
              const sourceHref = firstSource ? (`/source-documents/${firstSource.source_document_id}` as Route) : null;

              return (
                <article className="trace-card" key={cluster.evidence_id}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        {cluster.event_count}개 뉴스 · 원천 {cluster.source_document_count}개 · {cluster.created_at}
                      </span>
                      <h3>{koCode(cluster.theme_key)} 저장 분석</h3>
                    </div>
                    <span className="relation-pill">{formatClusterRagStatus(cluster)}</span>
                  </div>

                  <div className="evidence-strip">
                    <span>분석 경계</span>
                    <strong>{koCode(cluster.extraction_run.provider)} · {koCode(cluster.extraction_run.model_id)}</strong>
                    <p>
                      저장된 AI 증거 {cluster.evidence_id}는 뉴스 묶음의 구조화 결과다. 비용은 $
                      {cluster.extraction_run.estimated_cost_usd.toFixed(4)}이고, 이 화면은 추천 점수나 주문을 바꾸지 않는다.
                    </p>
                  </div>

                  <div className="trace-chain" aria-label={`${koCode(cluster.theme_key)} 저장 AI 뉴스 묶음 흐름`}>
                    <div className="trace-node">
                      <span>수집</span>
                      <strong>RSS 뉴스 {cluster.event_count}개</strong>
                      <p>{formatDirectionCounts(cluster.direction_counts)}</p>
                    </div>

                    <div className="trace-arrow" aria-hidden="true">→</div>

                    <div className="trace-node">
                      <span>분석</span>
                      <strong>{koCode(cluster.theme_key)}</strong>
                      <p>대표 이벤트 {cluster.representative_event_id ?? "대기"} · 신뢰도 {formatPercent(cluster.confidence)}</p>
                    </div>

                    <div className="trace-arrow" aria-hidden="true">→</div>

                    <div className="trace-node">
                      <span>검색 준비</span>
                      <strong>
                        청크 {cluster.chunk_count}개 · 임베딩 {cluster.embedded_chunk_count}개
                      </strong>
                      <p>저장된 뉴스 원문 조각이 이 묶음의 근거로 연결되어 있다.</p>
                    </div>

                    <div className="trace-arrow" aria-hidden="true">→</div>

                    <div className="trace-node trace-node-final">
                      <span>검토</span>
                      <strong>{formatSymbols(cluster.symbols)}</strong>
                      <p>종목 상세와 AI 근거 화면에서 원천 문서와 분석 결과를 함께 확인한다.</p>
                      <div className="mini-link-stack">
                        <Link href={evidenceHref}>AI 근거</Link>
                        {stockHref ? <Link href={stockHref}>종목 상세</Link> : null}
                        {sourceHref ? <Link href={sourceHref}>원천 문서</Link> : null}
                      </div>
                    </div>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 저장 뉴스와 원천`}>
                    <span>대표 뉴스와 원천 문서</span>
                    <div className="relationship-list">
                      {cluster.events.slice(0, 3).map((event) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <strong>{koLabel(event.title)}</strong>
                          <small>
                            {koCode(event.symbol)} · 영향도 {formatPercent(event.impact_score)}
                          </small>
                        </div>
                      ))}
                      {cluster.source_documents.slice(0, 3).map((document) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${document.source_document_id}`}>
                          <span>원천</span>
                          <strong>{koLabel(document.title || document.source_document_id)}</strong>
                          <small>
                            청크 {document.chunk_count} · 임베딩 {document.embedded_chunk_count} · {document.published_at}
                          </small>
                        </div>
                      ))}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <article className="trace-card" style={{ marginTop: "18px" }}>
            <div className="trace-card-top">
              <div>
                <span className="metric-sub">저장 대기</span>
                <h3>아직 저장된 AI 뉴스 묶음이 없다.</h3>
              </div>
            </div>
            <p className="relationship-empty">뉴스 수집, 이벤트 구조화, 뉴스 묶음 생성이 성공하면 이 영역이 채워진다.</p>
          </article>
        )}
      </section>

      <section className="intelligence-board reveal delay-2" aria-labelledby="news-cluster-title">
        <div className="section-heading stacked-heading">
          <span>오늘의 연결 구조</span>
          <h2 id="news-cluster-title">뉴스 묶음 분석</h2>
        </div>

        {newsClusters.length > 0 ? (
          <div className="trace-grid">
            {newsClusters.map((cluster) => (
              <article className="trace-card" key={cluster.key}>
                <div className="trace-card-top">
                  <div>
                    <span className="metric-sub">
                      {cluster.eventCount}개 뉴스 · {cluster.sourceDocumentCount}개 원천 · 최신 {cluster.latestAt}
                    </span>
                    <h3>{koCode(cluster.themeKey)}</h3>
                  </div>
                  <span className="relation-pill">{formatClusterTone(cluster)}</span>
                </div>

                <div className="evidence-strip">
                  <span>분석 방식</span>
                  <strong>무료 로컬 규칙</strong>
                  <p>
                    RSS 출처, 제목/요약 키워드, 같은 테마/종목 관계로 묶었다. 이 요약은 투자 결론이나 주문 신호가
                    아니라 사람이 검토할 뉴스 지도다.
                  </p>
                </div>

                <div className="trace-chain" aria-label={`${koCode(cluster.themeKey)} 뉴스 묶음 분석 흐름`}>
                  <div className="trace-node">
                    <span>발생</span>
                    <strong>뉴스 {cluster.eventCount}개</strong>
                    <p>오늘 수집된 RSS 뉴스 중 같은 테마로 분류된 항목을 묶었다.</p>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node">
                    <span>분류</span>
                    <strong>{koCode(cluster.themeKey)}</strong>
                    <p>RSS 출처 성격과 헤드라인 키워드를 사용해 1차 테마를 붙였다.</p>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node">
                    <span>종목</span>
                    <strong>{formatSymbols(cluster.symbols)}</strong>
                    <p>명확한 종목 코드 또는 시장 대용 지표가 있는 경우에만 연결한다.</p>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node trace-node-final">
                    <span>관계</span>
                    <strong>{formatRelationTypes(cluster.relationTypes)}</strong>
                    <p>같은 테마, 같은 종목, 같은 원천 문서 관계가 있으면 함께 추적한다.</p>
                  </div>
                </div>

                <div className="relationship-panel" aria-label={`${koCode(cluster.themeKey)} 대표 뉴스`}>
                  <span>대표 뉴스</span>
                  <div className="relationship-list">
                    {cluster.examples.map((event) => (
                      <div className="relationship-chip" key={`${cluster.key}-${event.event_id}`}>
                        <span>{koCode(event.impact_direction)}</span>
                        <strong>{koLabel(event.title)}</strong>
                        <small>
                          {koCode(event.symbol)} · {koCode(event.event_type)} · 영향도 {formatPercent(event.impact_score)}
                        </small>
                        <small>품질 관문 {koCode(event.quality_gate)}</small>
                      </div>
                    ))}
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <article className="trace-card">
            <div className="trace-card-top">
              <div>
                <span className="metric-sub">수집 대기</span>
                <h3>오늘 표시할 뉴스 묶음이 아직 없다.</h3>
              </div>
            </div>
            <p className="relationship-empty">
              뉴스 수집과 뉴스 분류 단발 실행이 성공하면 이 영역에 테마/종목별 뉴스 묶음이 표시된다.
            </p>
          </article>
        )}
      </section>

      <section className="intelligence-board reveal delay-2" aria-labelledby="trace-title">
        <div className="section-heading stacked-heading">
          <span>추적 흐름 — 이벤트에서 검토까지</span>
          <h2 id="trace-title">대표 이벤트 5개만 검토 흐름으로 보여준다</h2>
        </div>

        <div className="trace-grid">
          {tracedEvents.map((event) => {
            const cycle = cycleByTheme.get(event.theme_key);
            const themeInstrument = event.theme_key === theme.theme_key ? themeInstrumentBySymbol.get(event.symbol) : null;
            const position = positionBySymbol.get(event.symbol);
            const paperAction = paperActionBySymbol.get(event.symbol);
            const relatedEvents = event.related_events ?? [];
            const evidenceHref = maybeRoute(event.ai_evidence_id ? `/ai-evidence/${event.ai_evidence_id}` : null);
            const documentHref = maybeRoute(event.source_document_id ? `/source-documents/${event.source_document_id}` : null);
            const themeHref = maybeRoute(`/themes/${event.theme_key}`);
            const recommendationHref = maybeRoute(
              themeInstrument?.latest_recommendation_id
                ? `/recommendations/${themeInstrument.latest_recommendation_id}`
                : paperAction?.recommendation_id
                  ? `/recommendations/${paperAction.recommendation_id}`
                  : null,
            );
            const thesisHref = maybeRoute(
              themeInstrument?.active_thesis_id
                ? `/theses/${themeInstrument.active_thesis_id}`
                : paperAction?.linked_thesis_id
                  ? `/theses/${paperAction.linked_thesis_id}`
                  : null,
            );

            return (
              <article className="trace-card" key={event.event_id}>
                <div className="trace-card-top">
                  <div>
                    <span className="metric-sub">
                      {koCode(event.symbol)} • {event.event_at} • {koCode(event.event_type)}
                    </span>
                    <h3>{koLabel(event.title)}</h3>
                  </div>
                  <span className="relation-pill">{koCode(event.impact_direction)}</span>
                </div>

                <div className="trace-chain" aria-label={`${event.title} 분석 흐름`}>
                  <div className="trace-node">
                    <span>발생</span>
                    <strong>뉴스/공시 이벤트</strong>
                    <p>
                      영향도 {formatPercent(event.impact_score)} · 품질 관문 {koCode(event.quality_gate)}
                    </p>
                    <div className="mini-link-stack">
                      <Link href="/events">이벤트 원장</Link>
                      {documentHref ? <Link href={documentHref}>원천 문서</Link> : null}
                    </div>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node">
                    <span>해석</span>
                    <strong>{aiAttached && event.ai_evidence_id ? aiEvidenceLabel(event.ai_evidence_type) : "AI 분석 대기"}</strong>
                    <p>
                      {event.ai_evidence_provider
                        ? `${koCode(event.ai_evidence_provider)}가 원천, 추출 필드, 신뢰도 ${formatPercent(event.ai_evidence_confidence)}를 증거로 저장했다.`
                        : "AI는 결론을 내리지 않고 원천 청크, 추출 필드, 신뢰도, 비용을 증거로 저장한다."}
                    </p>
                    <div className="mini-link-stack">
                      {evidenceHref ? <Link href={evidenceHref}>{aiEvidenceLabel(event.ai_evidence_type)} 열기</Link> : <span>연결된 AI 근거 없음</span>}
                    </div>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node">
                    <span>연결</span>
                    <strong>{koCode(event.theme_key)}</strong>
                    <p>
                      사이클 {koCode(cycle?.state ?? theme.state)} · 신뢰도 {formatPercent(cycle?.confidence ?? theme.confidence)}
                    </p>
                    <div className="mini-link-stack">
                      {themeHref ? <Link href={themeHref}>테마 상세</Link> : null}
                      <Link href="/cycles">사이클 보드</Link>
                    </div>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node">
                    <span>판단</span>
                    <strong>추천/투자 논리</strong>
                    <p>
                      추천과 투자 논리는 자동 주문이 아니라 점수, 증거, 무효화 조건을 같이 저장한 검토 대상이다.
                    </p>
                    <div className="mini-link-stack">
                      {recommendationHref ? <Link href={recommendationHref}>추천 검토서</Link> : <span>추천 연결 없음</span>}
                      {thesisHref ? <Link href={thesisHref}>투자 논리</Link> : <span>투자 논리 연결 없음</span>}
                    </div>
                  </div>

                  <div className="trace-arrow" aria-hidden="true">→</div>

                  <div className="trace-node trace-node-final">
                    <span>검토</span>
                    <strong>보유/가상 거래 안전</strong>
                    <p>
                      보유 {position ? koCode(position.coverage_status) : "미보유"} · 조치{" "}
                      {position ? koCode(position.action) : "검토 없음"} · 가상{" "}
                      {paperAction ? koCode(paperAction.paper_action) : "대상 없음"}
                    </p>
                    <div className="mini-link-stack">
                      <Link href="/portfolio/coverage">보유 검토</Link>
                      <Link href="/paper-trading">가상 거래</Link>
                    </div>
                  </div>
                </div>

                {paperAction ? (
                  <div className="evidence-strip">
                    <span>가상 거래 판정</span>
                    <strong>{koCode(paperAction.paper_action)}</strong>
                    <p>
                      {koReason(paperAction.reason)} · 위험도 {koCode(paperAction.risk_level)} · 사람 승인{" "}
                      {paperAction.requires_human_approval ? "필요" : "불필요"}
                    </p>
                  </div>
                ) : null}

                {relatedEvents.length > 0 ? (
                  <div className="relationship-panel" aria-label={`${event.title} 관계 그래프`}>
                    <span>관계 그래프</span>
                    <div className="relationship-list">
                      {relatedEvents.map((related) => (
                        <div className="relationship-chip" key={`${event.event_id}-${related.event_id}`}>
                          <span>{koCode(related.relation_type)}</span>
                          <strong>{koLabel(related.title)}</strong>
                          <small>
                            {koCode(related.symbol)} · {koCode(related.theme_key)} · 강도{" "}
                            {formatPercent(related.relation_strength)}
                          </small>
                          <small>{koLabel(related.reason)}</small>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : null}
              </article>
            );
          })}
        </div>
        {hiddenTraceCount > 0 ? (
          <p className="flow-note">
            나머지 이벤트 {hiddenTraceCount}개는 반복 설명을 줄이기 위해 여기서 숨겼다. 전체 뉴스와 공시 원장은{" "}
            <Link href="/events">뉴스 원장</Link>에서 확인한다.
          </p>
        ) : null}
      </section>

      <section className="flow-panel reveal delay-3" aria-labelledby="ai-boundary-title">
        <div className="section-heading flow-heading">
          <span>AI 사용 경계</span>
          <h2 id="ai-boundary-title">AI 분석은 붙어 있지만, 아직 투자 결론 엔진은 아니다</h2>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>01</span>
            <strong>원천 제한</strong>
            <p>현재 화면의 뉴스/공시 추적은 SEC 공시와 무료 RSS 뉴스 중심이다. 유료 뉴스 API는 사용하지 않는다.</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>AI 역할</strong>
            <p>AI는 원천 문서를 구조화하고 근거를 남긴다. RSS 묶음은 무료 로컬 규칙 보조 증거이고, 중요 뉴스 후보는 Codex OAuth batch 분석으로 저장된다.</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>연관 추적</strong>
            <p>이벤트는 테마, 종목, 추천, 투자 논리, 포트폴리오 검토와 연결되어야 의미가 생긴다.</p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>다음 보강</strong>
            <p>다음 단계는 이 묶음 분석을 저장 가능한 AI 검색 지식베이스와 관계 지도 증거로 승격하는 것이다.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
