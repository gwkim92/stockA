import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
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
type AiNewsClusterSummary = AiNewsClusterListData["summary"];
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

function isLocalRuleCluster(cluster: StoredAiNewsCluster) {
  return ["local_rules", "local_deterministic"].includes(cluster.extraction_run.provider);
}

function formatClusterRunMode(cluster: StoredAiNewsCluster) {
  if (isLocalRuleCluster(cluster)) {
    return "로컬 규칙 묶음";
  }
  if (cluster.extraction_run.provider === "codex_oauth") {
    return "LLM 묶음";
  }
  return koCode(cluster.extraction_run.provider);
}

function formatClusterHeadline(cluster: StoredAiNewsCluster) {
  const storyLabel = formatClusterStory(cluster);
  const isUntranslatedStory = storyLabel === cluster.story_label && storyLabel !== koCode(cluster.theme_key);
  if (isLocalRuleCluster(cluster) && hasStorySplit(cluster) && isUntranslatedStory) {
    return `${koCode(cluster.theme_key)} 하위 이슈`;
  }
  return storyLabel;
}

function formatStoryKeyword(cluster: StoredAiNewsCluster) {
  if (!isLocalRuleCluster(cluster) || !hasStorySplit(cluster)) {
    return null;
  }
  const label = cluster.story_label?.trim();
  if (!label || label === cluster.theme_key || label === cluster.theme_name) {
    return null;
  }
  return `원문 키워드: ${label}`;
}

function formatLlmCandidateStatus(summary: AiNewsClusterSummary) {
  if (summary.llm_candidate_invocation_count === 0) {
    return "LLM 실행 없음";
  }
  if (summary.latest_llm_invocation_status === "failed") {
    return "최근 LLM 실패";
  }
  if (summary.latest_llm_invocation_status === "succeeded") {
    return "최근 LLM 성공";
  }
  return koCode(summary.latest_llm_invocation_status);
}

function formatLlmCandidateDetail(summary: AiNewsClusterSummary) {
  return `성공 artifact ${summary.llm_candidate_artifact_count}건 · 성공 호출 ${summary.llm_candidate_success_count}건 · 실패 호출 ${summary.llm_candidate_failed_count}건`;
}

function formatClusterModeStatus(summary: AiNewsClusterSummary) {
  if (summary.cluster_count === 0) {
    return "묶음 없음";
  }
  if (summary.local_rule_cluster_count === summary.cluster_count) {
    return "규칙 기반";
  }
  return `규칙 ${summary.local_rule_cluster_count}/${summary.cluster_count}`;
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
  const clusterSummary = storedNewsClusters.summary;
  const newsRun = findNewsPipelineRun(dataHealth);
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
            어떤 뉴스가 왜 묶였고, 어떤 종목·테마에 연결됐는지 본다.
          </h1>
        </div>
        <p className="page-lede">
          뉴스 묶음의 기준, 직접 연결 종목, 상위 흐름 전파 여부, 원천 문서를 한 카드에서 확인한다.
          AI는 주문을 내리지 않고 뉴스의 종목·테마·방향·불확실성만 구조화한다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="뉴스 AI 판단 요약">
        <article className="rail-cell">
          <span>뉴스 수집</span>
          <strong className="rail-word-value">{formatRunStatus(newsRun)}</strong>
          <small>{formatNewsRunLabel(newsRun)} · {newsRun?.finished_at ?? "최근 완료 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>LLM 후보 분석</span>
          <strong className="rail-word-value">{formatLlmCandidateStatus(clusterSummary)}</strong>
          <small>{formatLlmCandidateDetail(clusterSummary)}</small>
        </article>
        <article className="rail-cell">
          <span>뉴스 묶음 방식</span>
          <strong className="rail-word-value">{formatClusterModeStatus(clusterSummary)}</strong>
          <small>배치 작업이 저장한 결과만 읽음</small>
        </article>
        <article className="rail-cell">
          <span>저장된 뉴스 묶음</span>
          <strong>{clusterSummary.cluster_count}</strong>
          <small>뉴스 {clusterSummary.clustered_event_count}개 연결</small>
        </article>
        <article className="rail-cell">
          <span>보유 커버리지</span>
          <strong className="rail-ratio-value">{formatPercent(dashboard.latest_metrics.weight_coverage_ratio)}</strong>
          <small>추천·보유 판단 연결률</small>
        </article>
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
          <h2 id="news-decision-board-title">묶음 기준과 종목 연결 이유를 먼저 보여준다</h2>
        </div>

        <section className="status-rail compact-rail" aria-label="뉴스 판단 보드 저장 상태">
          <article className="rail-cell">
            <span>묶음 증거</span>
            <strong>{clusterSummary.cluster_count}</strong>
            <small>저장된 AI/규칙 증거</small>
          </article>
          <article className="rail-cell">
            <span>검색 조각</span>
            <strong>{clusterSummary.chunk_count}</strong>
            <small>임베딩 {clusterSummary.embedded_chunk_count}개</small>
          </article>
          <article className="rail-cell">
            <span>분석 비용</span>
            <strong>${clusterSummary.estimated_cost_usd.toFixed(4)}</strong>
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
              const storyLabel = formatClusterHeadline(cluster);
              const storyKeyword = formatStoryKeyword(cluster);
              const splitByStory = hasStorySplit(cluster);

              return (
                <article className="news-decision-card" key={cluster.evidence_id}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        뉴스 {cluster.event_count}개 · 원천 {cluster.source_document_count}개 · {formatClusterRunMode(cluster)} · {cluster.created_at}
                      </span>
                      <h3>{storyLabel}</h3>
                      <p className="cluster-story-context">
                        상위 테마: {koCode(cluster.theme_key)}
                        {storyKeyword ? ` · ${storyKeyword}` : ""}
                      </p>
                    </div>
                    <span className="relation-pill">{formatClusterRagStatus(cluster)}</span>
                  </div>

                  <div className="cluster-decision-grid" aria-label={`${koCode(cluster.theme_key)} 판단 요약`}>
                    <div className="cluster-decision-cell">
                      <span>무슨 일이 있었나</span>
                      <strong>
                        {cluster.event_count}개 뉴스가 같은 {splitByStory ? "이슈" : "테마"}로 묶였다
                      </strong>
                      <p>
                        {formatClusterRunMode(cluster)} 기준이다. 대표 이벤트 {cluster.representative_event_id ?? "대기"}를
                        중심으로 흐름을 추적한다.
                      </p>
                    </div>
                    <div className="cluster-decision-cell">
                      <span>방향성</span>
                      <strong>{formatDirectionCounts(cluster.direction_counts)}</strong>
                      <p>신뢰도 {formatPercent(cluster.confidence)}. 방향이 약하면 투자 입력으로 승격하지 않는다.</p>
                    </div>
                    <div className="cluster-decision-cell">
                      <span>직접 종목 / 전파 후보</span>
                      <strong>{formatSymbols(cluster.symbols)}</strong>
                      <p>직접 종목 뉴스는 종목에 바로 붙고, 거시·테마 뉴스는 상위 흐름 전파로 종목 영향을 계산한다.</p>
                    </div>
                    <div className="cluster-decision-cell cluster-decision-final">
                      <span>다음 판단</span>
                      <strong>추천·보유 검토의 근거 후보</strong>
                      <p>AI 증거 상세에서 원천 문서와 추출 필드가 맞는지 먼저 확인한다.</p>
                    </div>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 묶음 근거`}>
                    <span>왜 이 뉴스들이 같이 묶였나</span>
                    <div className="relationship-list">
                      {cluster.relation_reasons.map((reason) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${reason}`}>
                          <span>근거</span>
                          <strong>{reason}</strong>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 대표 뉴스`}>
                    <span>대표 뉴스</span>
                    <div className="relationship-list">
                      {cluster.events.slice(0, 3).map((event) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <NewsTitleBlock
                            compact
                            title={event.title}
                            symbol={event.symbol}
                            themeKey={cluster.theme_key}
                            impactDirection={event.impact_direction}
                            impactScore={event.impact_score}
                          />
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
                    저장된 뉴스 묶음 증거가 아직 없어서 로컬 규칙 기반 임시 묶음을 보여준다.
                    AI 배치가 성공하면 묶음 기준과 원천 문서가 있는 증거 카드로 대체된다.
                  </p>
                  <div className="relationship-panel" aria-label={`${koCode(cluster.themeKey)} 임시 묶음 근거`}>
                    <span>왜 묶였나</span>
                    <div className="relationship-list">
                      <div className="relationship-chip">
                        <span>테마</span>
                        <strong>같은 상위 테마로 임시 묶음: {koCode(cluster.themeKey)}</strong>
                      </div>
                      {cluster.symbols.length > 0 ? (
                        <div className="relationship-chip">
                          <span>종목</span>
                          <strong>직접 연결 종목: {cluster.symbols.map(koCode).join(", ")}</strong>
                        </div>
                      ) : (
                        <div className="relationship-chip">
                          <span>상위 흐름</span>
                          <strong>직접 종목 없이 시장/테마 흐름으로 표시</strong>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="relationship-panel" aria-label={`${koCode(cluster.themeKey)} 임시 대표 뉴스`}>
                    <span>대표 뉴스</span>
                    <div className="relationship-list">
                      {cluster.examples.map((event) => (
                        <div className="relationship-chip" key={`${cluster.key}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <NewsTitleBlock
                            compact
                            title={event.title}
                            symbol={event.symbol}
                            themeKey={event.theme_key}
                            impactDirection={event.impact_direction}
                            impactScore={event.impact_score}
                          />
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
                    <NewsTitleBlock
                      title={event.title}
                      symbol={event.symbol}
                      themeKey={event.theme_key}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
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
                  <NewsTitleBlock
                    compact
                    title={event.title}
                    symbol={event.symbol}
                    themeKey={event.theme_key}
                    impactDirection={event.impact_direction}
                    impactScore={event.impact_score}
                  />
                  <small>
                    {formatNewsSymbol(event.symbol)} · {koCode(event.theme_key)} · {event.event_at}
                  </small>
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </section>

    </div>
  );
}
