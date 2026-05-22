import Link from "next/link";
import type { Route } from "next";

import {
  getAiNewsClusters,
  getCockpitSnapshot,
  getDataHealth,
  getEvents,
} from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiNewsClusterListData, DataHealthData, EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "뉴스·AI 판단" };

type NewsEvent = EventListData["events"][number];
type StoredAiNewsCluster = AiNewsClusterListData["clusters"][number];
type PipelineRun = DataHealthData["pipeline_runs"][number];

type FallbackNewsCluster = {
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
  examples: NewsEvent[];
};

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function isKnownCode(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function maybeRoute(path: string | null | undefined) {
  return path ? (path as Route) : null;
}

function aiEvidenceLabel(type: string | null) {
  if (type === "news_event_candidate") {
    return "개별 뉴스 AI 후보";
  }
  if (type === "news_cluster_summary") {
    return "뉴스 묶음 증거";
  }
  if (type) {
    return koCode(type);
  }
  return "AI 분석 대기";
}

function formatSymbols(symbols: string[]) {
  const knownSymbols = symbols.filter(isKnownCode);
  if (knownSymbols.length === 0) {
    return "시장/테마 뉴스";
  }
  return knownSymbols.slice(0, 5).map(koCode).join(", ");
}

function formatNewsSymbol(symbol: string | null | undefined) {
  return isKnownCode(symbol) ? koCode(symbol) : "시장/테마 뉴스";
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

function formatClusterStory(cluster: StoredAiNewsCluster) {
  const label = cluster.story_label?.trim();
  if (!label || label === cluster.theme_key || label === cluster.theme_name) {
    return koCode(cluster.theme_key);
  }
  return koLabel(label);
}

function hasStorySplit(cluster: StoredAiNewsCluster) {
  return Boolean(cluster.story_key && cluster.story_key !== "theme");
}

function formatFallbackTone(cluster: FallbackNewsCluster) {
  const parts = [
    cluster.supportiveCount > 0 ? `우호 ${cluster.supportiveCount}` : null,
    cluster.riskReviewCount > 0 ? `리스크 ${cluster.riskReviewCount}` : null,
    cluster.watchCount > 0 ? `관찰 ${cluster.watchCount}` : null,
  ].filter(Boolean);
  return parts.length > 0 ? parts.join(" · ") : "영향 미분류";
}

function buildFallbackClusters(events: NewsEvent[]) {
  const clusters = new Map<
    string,
    FallbackNewsCluster & {
      symbolSet: Set<string>;
      sourceDocumentSet: Set<string>;
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
        examples: [],
        symbolSet: new Set<string>(),
        sourceDocumentSet: new Set<string>(),
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
    }))
    .sort((left, right) => {
      if (right.eventCount !== left.eventCount) {
        return right.eventCount - left.eventCount;
      }
      return right.latestAt.localeCompare(left.latestAt);
    })
    .slice(0, 4);
}

function findNewsPipelineRun(dataHealth: DataHealthData): PipelineRun | null {
  return (
    dataHealth.pipeline_runs.find((run) => run.job_id === "news-rss-daily")
    ?? dataHealth.pipeline_runs.find((run) => run.pipeline_name === "news_rss_upsert")
    ?? null
  );
}

function findAiPipelineRun(dataHealth: DataHealthData): PipelineRun | null {
  return (
    dataHealth.pipeline_runs.find((run) => run.pipeline_name === "event_intelligence_llm_extract")
    ?? dataHealth.pipeline_runs.find((run) => run.job_id === "event-intelligence-llm-extract")
    ?? null
  );
}

function formatRunStatus(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력 없음";
  }
  return `${koCode(run.latest_status)} · ${koCode(run.health_status)}`;
}

function formatNewsRunLabel(newsRun: PipelineRun | null) {
  if (!newsRun) {
    return "뉴스 RSS 수집";
  }
  return newsRun.job_id === "news-rss-daily" || newsRun.pipeline_name === "news_rss_upsert"
    ? "뉴스 RSS 수집"
    : koCode(newsRun.job_id);
}

function clusterEvidenceHref(cluster: StoredAiNewsCluster) {
  return `/ai-evidence/${encodeURIComponent(cluster.evidence_id)}` as Route;
}

function sourceDocumentHref(documentId: string | null | undefined) {
  return documentId ? (`/source-documents/${encodeURIComponent(documentId)}` as Route) : null;
}

function stockHref(symbol: string | null | undefined) {
  return isKnownCode(symbol) ? (`/stocks/${encodeURIComponent(symbol as string)}` as Route) : null;
}

export default async function IntelligencePage() {
  const [dataHealthResponse, cockpitSnapshot, eventsResponse, newsClusterResponse] = await Promise.all([
    getDataHealth(),
    getCockpitSnapshot(),
    getEvents({ limit: 40 }),
    getAiNewsClusters({ limit: 4 }),
  ]);

  const dataHealth = dataHealthResponse.data;
  const dashboard = cockpitSnapshot.dashboard.data;
  const events = eventsResponse.data;
  const storedNewsClusters = newsClusterResponse.data;
  const newsRun = findNewsPipelineRun(dataHealth);
  const aiRun = findAiPipelineRun(dataHealth);
  const fallbackClusters = buildFallbackClusters(events.events);
  const aiCandidateEvents = events.events
    .filter((event) => event.ai_evidence_id && event.ai_evidence_type === "news_event_candidate")
    .slice(0, 6);
  const unstructuredEvents = events.events.filter((event) => !event.ai_evidence_id).slice(0, 3);
  const firstCandidateEvidenceId = aiCandidateEvents[0]?.ai_evidence_id ?? null;
  const activation = dataHealth.scheduler.activation;

  const detailLinks = [
    {
      title: "개별 뉴스 AI 후보",
      copy: "AI가 한 뉴스에서 추출한 종목, 테마, 방향, 불확실성을 확인한다.",
      href: firstCandidateEvidenceId ? `/ai-evidence/${firstCandidateEvidenceId}` : "/ai-evidence",
    },
    {
      title: "뉴스·이벤트 원장",
      copy: "수집된 모든 뉴스와 공시, 원천 문서, 관련 이벤트를 확인한다.",
      href: "/events",
    },
    {
      title: "종목 확인실",
      copy: "가격 캔들, 보유 여부, 추천 연결, 최근 뉴스를 종목별로 본다.",
      href: "/stocks",
    },
    {
      title: "추천·보유 검토",
      copy: "AI 증거가 추천 점수와 보유 검토에 실제로 붙었는지 본다.",
      href: "/recommendations",
    },
  ];

  return (
    <div className="terminal-page intelligence-page">
      <section className="page-hero reveal" aria-labelledby="intelligence-title">
        <div>
          <div className="bento-badge">뉴스·AI 판단</div>
          <h1 className="page-title" id="intelligence-title">
            뉴스와 AI는 여기서 한 번만 판단한다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 뉴스 요약, AI 후보, 이벤트 원장을 반복해서 보여주지 않는다. 먼저 저장된 뉴스 묶음으로
          “오늘 시장에서 무엇이 움직였는지”를 보고, 필요한 경우에만 개별 AI 후보와 원천 문서로 내려간다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="뉴스 AI 판단 요약">
        <article className="rail-cell">
          <span>뉴스 수집</span>
          <strong className="rail-word-value">{formatRunStatus(newsRun)}</strong>
          <small>{formatNewsRunLabel(newsRun)} · {newsRun?.finished_at ?? "최근 완료 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>AI 후보 분석</span>
          <strong className="rail-word-value">{formatRunStatus(aiRun)}</strong>
          <small>{aiRun?.finished_at ?? "최근 완료 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>저장된 뉴스 묶음</span>
          <strong>{storedNewsClusters.summary.cluster_count}</strong>
          <small>뉴스 {storedNewsClusters.summary.clustered_event_count}개 연결</small>
        </article>
        <article className="rail-cell">
          <span>보유 커버리지</span>
          <strong className="rail-ratio-value">{formatPercent(dashboard.latest_metrics.weight_coverage_ratio)}</strong>
          <small>추천·보유 판단 연결률</small>
        </article>
      </section>

      <section className="flow-panel reveal delay-2" aria-labelledby="intelligence-reading-order">
        <div className="section-heading flow-heading">
          <span>읽는 법</span>
          <h2 id="intelligence-reading-order">카드가 많아도 판단 순서는 세 단계다</h2>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>01</span>
            <strong>뉴스 묶음부터 본다</strong>
            <p>개별 기사보다 같은 테마로 모인 흐름이 더 중요하다. 이 영역이 오늘의 핵심 신호다.</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>AI 후보는 근거 검증용이다</strong>
            <p>AI는 주문 결론을 내리지 않는다. 종목, 테마, 방향, 신뢰도, 불확실성을 구조화한다.</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>추천·보유로 연결된 것만 판단한다</strong>
            <p>추천 점수나 보유 검토에 연결되지 않은 뉴스는 정보일 뿐이며, 투자 행동으로 승격하지 않는다.</p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>원장은 상세 화면으로 보낸다</strong>
            <p>모든 뉴스와 공시를 이 화면에 반복하지 않고 이벤트 원장, AI 후보, 종목 상세에서 확인한다.</p>
          </article>
        </div>
      </section>

      <section className="where-grid reveal delay-2" aria-label="상세 화면 역할">
        {detailLinks.map((link) => (
          <Link className="where-card" href={link.href as Route} key={link.title}>
            <span>상세</span>
            <strong>{link.title}</strong>
            <p>{link.copy}</p>
            <small>화면 열기</small>
          </Link>
        ))}
      </section>

      <section className="intelligence-board reveal delay-2" aria-labelledby="news-decision-board-title">
        <div className="section-heading stacked-heading">
          <span>뉴스 판단 보드</span>
          <h2 id="news-decision-board-title">대표 뉴스 묶음만 남기고 중복 원장은 숨긴다</h2>
        </div>

        <section className="status-rail compact-rail" aria-label="뉴스 판단 보드 저장 상태">
          <article className="rail-cell">
            <span>묶음 증거</span>
            <strong>{storedNewsClusters.summary.cluster_count}</strong>
            <small>저장된 AI/규칙 증거</small>
          </article>
          <article className="rail-cell">
            <span>검색 조각</span>
            <strong>{storedNewsClusters.summary.chunk_count}</strong>
            <small>임베딩 {storedNewsClusters.summary.embedded_chunk_count}개</small>
          </article>
          <article className="rail-cell">
            <span>분석 비용</span>
            <strong>${storedNewsClusters.summary.estimated_cost_usd.toFixed(4)}</strong>
            <small>화면에서 실시간 LLM 호출 없음</small>
          </article>
          <article className="rail-cell">
            <span>자동화 승인</span>
            <strong>{koCode(activation.status)}</strong>
            <small>{activation.activation_allowed ? "활성화 가능" : "운영 정책 대기"}</small>
          </article>
        </section>

        {storedNewsClusters.clusters.length > 0 ? (
          <div className="news-decision-grid">
            {storedNewsClusters.clusters.map((cluster) => {
              const firstSymbol = cluster.symbols.find(isKnownCode) ?? null;
              const firstSource = cluster.source_documents[0];
              const evidenceLink = clusterEvidenceHref(cluster);
              const stockLink = stockHref(firstSymbol);
              const sourceLink = sourceDocumentHref(firstSource?.source_document_id);
              const storyLabel = formatClusterStory(cluster);
              const splitByStory = hasStorySplit(cluster);

              return (
                <article className="news-decision-card" key={cluster.evidence_id}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        뉴스 {cluster.event_count}개 · 원천 {cluster.source_document_count}개 · {cluster.created_at}
                      </span>
                      <h3>{storyLabel}</h3>
                      <p className="cluster-story-context">상위 테마: {koCode(cluster.theme_key)}</p>
                    </div>
                    <span className="relation-pill">{formatClusterRagStatus(cluster)}</span>
                  </div>

                  <div className="cluster-decision-grid" aria-label={`${koCode(cluster.theme_key)} 판단 요약`}>
                    <div className="cluster-decision-cell">
                      <span>무슨 일이 있었나</span>
                      <strong>
                        {cluster.event_count}개 뉴스가 같은 {splitByStory ? "이슈" : "테마"}로 묶였다
                      </strong>
                      <p>대표 이벤트 {cluster.representative_event_id ?? "대기"} 기준으로 흐름을 추적한다.</p>
                    </div>
                    <div className="cluster-decision-cell">
                      <span>방향성</span>
                      <strong>{formatDirectionCounts(cluster.direction_counts)}</strong>
                      <p>신뢰도 {formatPercent(cluster.confidence)}. 방향이 약하면 투자 입력으로 승격하지 않는다.</p>
                    </div>
                    <div className="cluster-decision-cell">
                      <span>직접 종목 / 전파 후보</span>
                      <strong>{formatSymbols(cluster.symbols)}</strong>
                      <p>종목명이 직접 없으면 오류가 아니다. 상위 흐름은 노출도 전파를 거쳐 종목 상세와 추천 근거에 붙는다.</p>
                    </div>
                    <div className="cluster-decision-cell cluster-decision-final">
                      <span>다음 판단</span>
                      <strong>추천·보유 검토의 근거 후보</strong>
                      <p>AI 증거 상세에서 원천 문서와 추출 필드가 맞는지 먼저 확인한다.</p>
                    </div>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 대표 뉴스`}>
                    <span>대표 뉴스</span>
                    <div className="relationship-list">
                      {cluster.events.slice(0, 3).map((event) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <strong>{koLabel(event.title)}</strong>
                          <small>
                            {formatNewsSymbol(event.symbol)} · 영향도 {formatPercent(event.impact_score)}
                          </small>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="btn-row decision-actions">
                    <Link className="btn btn-primary" href={evidenceLink}>
                      AI 근거 상세
                    </Link>
                    {stockLink ? (
                      <Link className="btn btn-secondary" href={stockLink}>
                        종목 상세
                      </Link>
                    ) : null}
                    {sourceLink ? (
                      <Link className="btn btn-secondary" href={sourceLink}>
                        원천 문서
                      </Link>
                    ) : null}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="news-decision-grid">
            {fallbackClusters.length > 0 ? (
              fallbackClusters.map((cluster) => (
                <article className="news-decision-card fallback-news-card" key={cluster.key}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        임시 묶음 · 뉴스 {cluster.eventCount}개 · 원천 {cluster.sourceDocumentCount}개
                      </span>
                      <h3>{koCode(cluster.themeKey)}</h3>
                    </div>
                    <span className="relation-pill">{formatFallbackTone(cluster)}</span>
                  </div>
                  <p className="fallback-note">
                    저장된 AI 뉴스 묶음이 아직 없어서, 화면은 로컬 규칙 기반 임시 묶음을 대신 보여준다.
                    AI batch가 성공하면 이 카드는 저장 증거 카드로 대체된다.
                  </p>
                  <div className="relationship-panel" aria-label={`${koCode(cluster.themeKey)} 임시 대표 뉴스`}>
                    <span>대표 뉴스</span>
                    <div className="relationship-list">
                      {cluster.examples.map((event) => (
                        <div className="relationship-chip" key={`${cluster.key}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <strong>{koLabel(event.title)}</strong>
                          <small>
                            {formatNewsSymbol(event.symbol)} · {koCode(event.event_type)} · 영향도{" "}
                            {formatPercent(event.impact_score)}
                          </small>
                        </div>
                      ))}
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <article className="news-decision-card">
                <div className="trace-card-top">
                  <div>
                    <span className="metric-sub">수집 대기</span>
                    <h3>오늘 표시할 뉴스 묶음이 아직 없다.</h3>
                  </div>
                </div>
                <p className="relationship-empty">뉴스 수집과 AI 분석 batch가 성공하면 이 영역에 대표 흐름이 표시된다.</p>
              </article>
            )}
          </div>
        )}
      </section>

      <section className="intelligence-board reveal delay-3" aria-labelledby="ai-candidate-queue-title">
        <div className="section-heading stacked-heading">
          <span>개별 뉴스 후보 검토 큐</span>
          <h2 id="ai-candidate-queue-title">AI가 해석한 뉴스는 상세 화면에서 검증한다</h2>
        </div>
        <p className="board-intro">
          이 목록은 원장이 아니라 검토 입구다. 제목을 읽고 판단하지 말고, 상세 화면에서 원천 문서, 테마·종목 영향,
          불확실성, 추천 연결 여부를 확인한다.
        </p>

        {aiCandidateEvents.length > 0 ? (
          <div className="review-queue-list">
            {aiCandidateEvents.map((event) => {
              const evidenceLink = maybeRoute(event.ai_evidence_id ? `/ai-evidence/${event.ai_evidence_id}` : null);
              const documentLink = sourceDocumentHref(event.source_document_id);
              const symbolLink = stockHref(event.symbol);

              return (
                <article className="review-queue-item" key={`${event.event_id}-${event.ai_evidence_id}`}>
                  <div>
                    <span className="metric-sub">
                      {formatNewsSymbol(event.symbol)} · {koCode(event.theme_key)} · {event.event_at}
                    </span>
                    <strong>{koLabel(event.title)}</strong>
                    <p>
                      {aiEvidenceLabel(event.ai_evidence_type)} · {koCode(event.impact_direction)} · 신뢰도{" "}
                      {formatPercent(event.ai_evidence_confidence)}
                    </p>
                  </div>
                  <div className="review-queue-actions">
                    {evidenceLink ? <Link className="btn btn-primary" href={evidenceLink}>AI 후보 상세</Link> : null}
                    {symbolLink ? <Link className="btn btn-secondary" href={symbolLink}>종목</Link> : null}
                    {documentLink ? <Link className="btn btn-secondary" href={documentLink}>원천</Link> : null}
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="empty-state">AI 후보가 아직 없다. 뉴스 수집과 뉴스 AI 분석 실행 이력을 먼저 확인해야 한다.</div>
        )}

        {unstructuredEvents.length > 0 ? (
          <details className="secondary-details">
            <summary>아직 AI 후보가 아닌 최근 뉴스 {unstructuredEvents.length}개 보기</summary>
            <div className="relationship-list">
              {unstructuredEvents.map((event) => (
                <div className="relationship-chip" key={event.event_id}>
                  <span>{koCode(event.event_type)}</span>
                  <strong>{koLabel(event.title)}</strong>
                  <small>
                    {formatNewsSymbol(event.symbol)} · {koCode(event.theme_key)} · {event.event_at}
                  </small>
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </section>

      <section className="flow-panel reveal delay-3" aria-labelledby="ai-boundary-title">
        <div className="section-heading flow-heading">
          <span>AI 사용 경계</span>
          <h2 id="ai-boundary-title">AI는 분석 근거를 만들고, 주문은 만들지 않는다</h2>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>01</span>
            <strong>실시간 호출 없음</strong>
            <p>화면 진입 시 LLM을 부르지 않는다. AI 분석은 배치 작업이 저장한 결과만 읽는다.</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>검증 실패 차단</strong>
            <p>알 수 없는 종목·테마, 낮은 신뢰도, 근거 부족은 추천 입력으로 넘기지 않는다.</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>무료 데이터 우선</strong>
            <p>뉴스는 무료 RSS, 가격은 무료 provider 예산 안에서 수집한다. 유료 뉴스 API는 쓰지 않는다.</p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>투자 행동은 별도 관문</strong>
            <p>추천, 보유 검토, 가상 거래 안전장치가 모두 통과해야 다음 행동 후보가 된다.</p>
          </article>
        </div>
      </section>
    </div>
  );
}
