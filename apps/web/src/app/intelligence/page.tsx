import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip } from "@/components/research/MetricStrip";
import {
  getAiNewsClusters,
  getDashboardToday,
  getDataHealth,
  getEvents,
} from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiNewsClusterListData, DataHealthData, EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "뉴스 흐름과 투자 근거" };

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

function safeCount(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function isKnownCode(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function maybeRoute(path: string | null | undefined) {
  return path ? (path as Route) : null;
}

function aiEvidenceLabel(type: string | null) {
  if (type === "news_event_candidate") {
    return "개별 뉴스 투자 근거";
  }
  if (type === "news_cluster_summary") {
    return "뉴스 묶음 근거";
  }
  if (type) {
    return koCode(type);
  }
  return "근거 대기";
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
  return entries.map(([key, count]) => `${formatImpactDirection(key)} ${count}`).join(" · ");
}

function formatImpactDirection(value: string | null | undefined) {
  if (value === "risk_review") {
    return "리스크 확인";
  }
  return koCode(value);
}

function formatClusterRagStatus(cluster: StoredAiNewsCluster) {
  if (cluster.chunk_count === 0) {
    return "원문 근거 없음";
  }
  if (cluster.embedded_chunk_count > 0) {
    return "원문 근거 검색 가능";
  }
  return "원문 근거 있음";
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
    return "기본 묶음";
  }
  if (cluster.extraction_run.provider === "codex_oauth") {
    return "심화 분석 묶음";
  }
  return koCode(cluster.extraction_run.provider);
}

function clusterGroupingBasis(cluster: StoredAiNewsCluster) {
  if (hasStorySplit(cluster)) {
    return {
      label: "묶인 기준",
      title: "같은 하위 이슈",
      body: `${koCode(cluster.theme_key)} 안에서 ${formatClusterStory(cluster)} 흐름으로 묶었다.`,
    };
  }
  return {
    label: "묶인 기준",
    title: "같은 상위 테마",
    body: `${koCode(cluster.theme_key)} 테마에 속한 뉴스들을 한 흐름으로 묶었다.`,
  };
}

function clusterInstrumentConnection(cluster: StoredAiNewsCluster) {
  const symbols = cluster.symbols.filter(isKnownCode);
  if (symbols.length > 0) {
    return {
      label: "종목 관계",
      title: `${symbols.slice(0, 3).map(koCode).join(", ")} 직접 연결`,
      body:
        symbols.length > 3
          ? `직접 언급 종목 ${symbols.length}개가 있습니다. 가격·추천·보유 상태와 연결됩니다.`
          : "회사명이나 티커가 직접 잡힌 뉴스라 종목 상세와 추천 근거에 바로 연결된다.",
    };
  }
  return {
    label: "종목 관계",
    title: "시장/테마 흐름",
    body: "특정 회사를 억지로 붙이지 않는다. 상위 흐름 노출도에 따라 관련 종목 영향이 별도로 전파된다.",
  };
}

function clusterRecommendationUse(cluster: StoredAiNewsCluster) {
  if ((cluster.confidence ?? 0) < 0.55) {
    return {
      label: "추천 영향",
      title: "관찰 전용",
      body: "신뢰도가 낮아 추천 판단의 중심 근거로 쓰지 않는다.",
    };
  }
  if (cluster.event_count < 2) {
    return {
      label: "추천 영향",
      title: "단일 뉴스 근거",
      body: "뉴스 수가 적어 보조 근거로만 둔다. 반복 흐름이 쌓일 때 비중을 높인다.",
    };
  }
  return {
    label: "추천 영향",
    title: "근거 항목",
    body: "추천 상세·보유 상태에 연결될 수 있다. 최종 판단은 가격, 사이클, 투자 논리가 함께 결정한다.",
  };
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
  if (safeCount(summary.llm_candidate_invocation_count) === 0) {
    return "개별 투자 근거 없음";
  }
  if (summary.latest_llm_invocation_status === "failed") {
    return "최근 근거 분석 중단";
  }
  if (summary.latest_llm_invocation_status === "succeeded") {
    return "최근 근거 분석 성공";
  }
  return koCode(summary.latest_llm_invocation_status);
}

function formatLlmCandidateDetail(summary: AiNewsClusterSummary) {
  if (safeCount(summary.llm_candidate_invocation_count) === 0) {
    return "뉴스 흐름은 저장된 기본 근거를 표시 중";
  }
  return `투자 근거 ${safeCount(summary.llm_candidate_artifact_count)}건 · 통과 ${safeCount(summary.llm_candidate_success_count)}건 · 중단 ${safeCount(summary.llm_candidate_failed_count)}건`;
}

function formatClusterModeStatus(summary: AiNewsClusterSummary) {
  const clusterCount = safeCount(summary.cluster_count);
  const localRuleClusterCount = safeCount(summary.local_rule_cluster_count);
  if (clusterCount === 0) {
    return "묶음 없음";
  }
  if (localRuleClusterCount === clusterCount) {
    return "규칙 기반";
  }
  return `규칙 ${localRuleClusterCount}/${clusterCount}`;
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
  const [dataHealthResponse, dashboardResponse, eventsResponse, newsClusterResponse] = await Promise.all([
    getDataHealth(),
    getDashboardToday(),
    getEvents({ limit: 24 }),
    getAiNewsClusters({ limit: 3 }),
  ]);

  const dataHealth = dataHealthResponse.data;
  const dashboard = dashboardResponse.data;
  const events = eventsResponse.data;
  const storedNewsClusters = newsClusterResponse.data;
  const clusterSummary = storedNewsClusters.summary;
  const newsRun = findNewsPipelineRun(dataHealth);
  const fallbackClusters = buildFallbackClusters(events.events);
  const aiCandidateEvents = events.events
    .filter((event) => event.ai_evidence_id && event.ai_evidence_type === "news_event_candidate")
    .slice(0, 3);
  const unstructuredEvents = events.events.filter((event) => !event.ai_evidence_id).slice(0, 2);
  const firstCluster = storedNewsClusters.clusters[0] ?? null;
  const visibleNewsClusters = storedNewsClusters.clusters.slice(0, 2);
  const hiddenNewsClusterCount = Math.max(storedNewsClusters.clusters.length - visibleNewsClusters.length, 0);
  const clusterCount = safeCount(clusterSummary.cluster_count);
  const llmCandidateSuccessCount = safeCount(clusterSummary.llm_candidate_success_count);
  const eventsSummary = events.summary as typeof events.summary & Record<string, unknown>;
  const blockedCandidateCount =
    safeCount(eventsSummary.suppressed_low_signal_candidate_count)
    + safeCount(eventsSummary.rejected_candidate_count)
    + safeCount(eventsSummary.validator_blocked_candidate_count);
  const firstFlowTitle = firstCluster
    ? formatClusterHeadline(firstCluster)
    : fallbackClusters[0]
      ? koCode(fallbackClusters[0].themeKey)
      : "상위 흐름 대기";
  const firstFlowTarget = firstCluster ? formatSymbols(firstCluster.symbols) : "시장/테마 흐름";
  const firstFlowHref = firstCluster ? clusterEvidenceHref(firstCluster) : ("/cycle-map" as Route);
  return (
    <div className="terminal-page decision-page intelligence-page research-command-page">
      <DecisionSummary
        eyebrow={`뉴스 인텔리전스 · ${dashboard.as_of_date}`}
        title={`${clusterCount.toLocaleString("ko-KR")}개 핵심 흐름이 시장 판단을 바꾸고 있습니다.`}
        description="반복된 뉴스의 공통 원인과 영향을 묶어 보고, 반대 근거와 종목 연결까지 함께 확인합니다."
        primaryAction={{ href: firstFlowHref, label: firstCluster ? "주요 흐름 분석" : "사이클 지도" }}
        secondaryActions={[
          { href: "/ai-evidence" as Route, label: "AI 근거" },
          { href: "/events" as Route, label: "전체 뉴스" },
        ]}
        side={
          <div className="research-lead-snapshot">
            <span>가장 큰 뉴스 흐름</span>
            <strong>{firstFlowTitle}</strong>
            <small>{firstFlowTarget} · 추천 근거 연결률 {formatPercent(dashboard.latest_metrics.weight_coverage_ratio)}</small>
          </div>
        }
      />
      <MetricStrip
        label="뉴스 인텔리전스 현황"
        items={[
          { label: "뉴스 흐름", value: `${clusterCount}개`, context: formatClusterModeStatus(clusterSummary) },
          { label: "AI 근거 통과", value: `${llmCandidateSuccessCount}개`, context: formatLlmCandidateStatus(clusterSummary) },
          { label: "품질 차단", value: `${blockedCandidateCount}개`, context: blockedCandidateCount > 0 ? "추천 근거에서 제외" : "새 차단 없음" },
          { label: "뉴스 수집", value: formatRunStatus(newsRun), context: formatNewsRunLabel(newsRun) },
        ]}
      />

      <section className="intelligence-board reveal delay-2" id="today-flow" aria-labelledby="news-decision-board-title">
        <div className="section-heading stacked-heading">
          <span>주요 시장 흐름</span>
          <h2 id="news-decision-board-title">반복된 사건이 만든 공통 투자 환경</h2>
          <p>
            영향이 큰 흐름부터 정렬했습니다. 각 묶음에서 원문, 연결 근거, 영향을 받는 종목을 확인할 수 있습니다.
          </p>
        </div>

        {storedNewsClusters.clusters.length > 0 ? (
          <>
            <div className="news-decision-grid">
              {visibleNewsClusters.map((cluster) => {
                const firstSymbol = cluster.symbols.find(isKnownCode) ?? null;
                const firstSource = cluster.source_documents[0];
                const evidenceLink = clusterEvidenceHref(cluster);
                const stockLink = stockHref(firstSymbol);
                const sourceLink = sourceDocumentHref(firstSource?.source_document_id);
                const storyLabel = formatClusterHeadline(cluster);
                const storyKeyword = formatStoryKeyword(cluster);
                const splitByStory = hasStorySplit(cluster);
                const groupingBasis = clusterGroupingBasis(cluster);
                const instrumentConnection = clusterInstrumentConnection(cluster);
                const recommendationUse = clusterRecommendationUse(cluster);
                const visibleRelationReasons = cluster.relation_reasons.slice(0, 3);

                return (
                  <article className="news-decision-card" key={cluster.evidence_id}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        뉴스 {cluster.event_count}개 · 원천 {cluster.source_document_count}개 · {formatClusterRunMode(cluster)}
                      </span>
                      <h3>{storyLabel}</h3>
                      <p className="cluster-story-context">
                        상위 테마: {koCode(cluster.theme_key)}
                        {storyKeyword ? ` · ${storyKeyword}` : ""}
                      </p>
                    </div>
                    <span className="relation-pill">{formatClusterRagStatus(cluster)}</span>
                  </div>

                  <p className="cluster-plain-summary">
                    {cluster.event_count}개 뉴스가 같은 {splitByStory ? "하위 이슈" : "상위 테마"}로 묶였다.
                    방향은 {formatDirectionCounts(cluster.direction_counts)}이고, 대상은 {formatSymbols(cluster.symbols)}이다.
                    신뢰도는 {formatPercent(cluster.confidence)}다.
                  </p>

                  <div className="cluster-proof-grid" aria-label={`${koCode(cluster.theme_key)} 핵심 근거`}>
                    <article>
                      <span>{groupingBasis.label}</span>
                      <strong>{groupingBasis.title}</strong>
                      <p>{groupingBasis.body}</p>
                    </article>
                    <article>
                      <span>{instrumentConnection.label}</span>
                      <strong>{instrumentConnection.title}</strong>
                      <p>{instrumentConnection.body}</p>
                    </article>
                    <article>
                      <span>{recommendationUse.label}</span>
                      <strong>{recommendationUse.title}</strong>
                      <p>{recommendationUse.body}</p>
                    </article>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 묶음 근거`}>
                    <span>묶인 근거</span>
                    <div className="relationship-list">
                      {visibleRelationReasons.map((reason, index) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-reason-${index}`}>
                          <span>근거</span>
                          <strong>{koLabel(reason)}</strong>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="relationship-panel" aria-label={`${koCode(cluster.theme_key)} 대표 뉴스`}>
                    <span>대표 뉴스 1건</span>
                    <div className="relationship-list">
                      {cluster.events.slice(0, 1).map((event) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${event.event_id}`}>
                          <span>{formatImpactDirection(event.impact_direction)}</span>
                          <NewsTitleBlock
                            compact
                            title={event.title}
                            koreanTitle={event.korean_title}
                            koreanSummary={event.korean_summary}
                            translationConfidence={event.translation_confidence}
                            symbol={event.symbol}
                            themeKey={cluster.theme_key}
                            impactDirection={formatImpactDirection(event.impact_direction)}
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
                      묶음 상세 열기
                    </Link>
                    {stockLink ? (
                      <Link className="btn btn-secondary" href={stockLink}>
                        종목 화면
                      </Link>
                    ) : null}
                    {sourceLink ? (
                      <Link className="btn btn-secondary" href={sourceLink}>
                        뉴스 원문
                      </Link>
                    ) : null}
                  </div>
                  </article>
                );
              })}
            </div>
            <div className="btn-row decision-actions">
              <Link className="btn btn-secondary" href={"/events" as Route}>
                수집 뉴스 전체 보기
              </Link>
              <Link className="btn btn-secondary" href={"/ai-evidence" as Route}>
                근거 후보 전체 보기
              </Link>
              <Link className="btn btn-secondary" href={"/ai-evidence/results" as Route}>
                통과 결과 전체 보기
              </Link>
            </div>
            {hiddenNewsClusterCount > 0 ? (
              <p className="board-intro">
                나머지 뉴스 묶음 {hiddenNewsClusterCount}개는 근거 목록과 통과 결과에 정리되어 있습니다.
              </p>
            ) : null}
          </>
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
                    저장된 뉴스 흐름 근거가 부족하다. 현재는 테마와 대표 뉴스만 참고하고,
                    추천 판단에는 보수적으로 반영한다.
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
                          <span>{formatImpactDirection(event.impact_direction)}</span>
                          <NewsTitleBlock
                            compact
                            title={event.title}
                            koreanTitle={event.korean_title}
                            koreanSummary={event.korean_summary}
                            translationConfidence={event.translation_confidence}
                            symbol={event.symbol}
                            themeKey={event.theme_key}
                            impactDirection={formatImpactDirection(event.impact_direction)}
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
                <p className="relationship-empty">뉴스 근거가 쌓이면 이 영역에 대표 흐름이 표시된다.</p>
              </article>
            )}
          </div>
        )}
      </section>

      <section
        className="intelligence-board intelligence-brief-board decision-triage-board reveal delay-3"
        id="news-decision-triage"
        aria-labelledby="news-decision-triage-title"
      >
        <div className="section-heading stacked-heading">
          <span>02 판단 대기열</span>
          <h2 id="news-decision-triage-title">근거를 추천에 쓰기 전에 한 번에 판별한다</h2>
          <p>
            개별 근거, 차단 항목, 추천 연결 상태를 한 화면에 모았다. 통과한 뉴스라도 바로 주문으로 이어지지 않고,
            원문 근거와 종목 맥락, 가상 매매 검증을 다시 지난다.
          </p>
        </div>

        <div className="decision-triage-grid">
          <article className="decision-triage-column is-wide">
            <div className="decision-triage-head">
              <span>투자 근거 후보</span>
              <strong>{llmCandidateSuccessCount.toLocaleString("ko-KR")}건 통과</strong>
              <p>대표 3건만 먼저 보여준다. 전체 근거는 전용 목록에 있다.</p>
            </div>
            {aiCandidateEvents.length > 0 ? (
              <div className="review-queue-list compact-review-list">
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
                          compact
                          title={event.title}
                          koreanTitle={event.korean_title}
                          koreanSummary={event.korean_summary}
                          translationConfidence={event.translation_confidence}
                          symbol={event.symbol}
                          themeKey={event.theme_key}
                          impactDirection={formatImpactDirection(event.impact_direction)}
                          impactScore={event.impact_score}
                        />
                        <p>
                          {aiEvidenceLabel(event.ai_evidence_type)} · 방향 {formatImpactDirection(event.impact_direction)} · 신뢰도{" "}
                          {formatPercent(event.ai_evidence_confidence)}
                        </p>
                      </div>
                      <div className="review-queue-actions">
                        {evidenceLink ? <Link className="btn btn-primary" href={evidenceLink}>근거 상세</Link> : null}
                        {symbolLink ? <Link className="btn btn-secondary" href={symbolLink}>종목</Link> : null}
                        {documentLink ? <Link className="btn btn-secondary" href={documentLink}>원문</Link> : null}
                      </div>
                    </article>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">아직 표시할 투자 근거 후보가 없다. 데이터 상태에서 최근 뉴스 분석 실행을 보면 된다.</div>
            )}
          </article>

          <article className="decision-triage-column">
            <div className="decision-triage-head">
              <span>차단·오염 의심</span>
              <strong>{blockedCandidateCount.toLocaleString("ko-KR")}건</strong>
              <p>{blockedCandidateCount > 0 ? "추천 입력에서 제외된 이유를 보여준다." : "현재 노출된 차단 항목은 없다."}</p>
            </div>
            <div className="decision-triage-stack">
              <article className={blockedCandidateCount > 0 ? "brief-signal-card watch" : "brief-signal-card ready"}>
                <span>추천 제외 기준</span>
                <strong>원문 근거 우선</strong>
                <p>뉴스에 없는 티커, 낮은 신뢰도, 애매한 테마 연결은 추천 입력에서 제외한다.</p>
              </article>
              <article className="brief-signal-card">
                <span>수집 상태</span>
                <strong>{formatRunStatus(newsRun)}</strong>
                <p>수집·분석 이상은 데이터 상태 화면에서 원인과 복구 상태로 분리된다.</p>
              </article>
            </div>
          </article>

          <article className="decision-triage-column">
            <div className="decision-triage-head">
              <span>추천 연결</span>
              <strong>{formatPercent(dashboard.latest_metrics.weight_coverage_ratio)}</strong>
              <p>추천 상세에서는 직접 뉴스, 상위 흐름, 가격·사이클 근거가 분리되어 표시됩니다.</p>
            </div>
            <div className="decision-triage-stack">
              <article className="brief-signal-card watch">
                <span>거래 경계</span>
                <strong>읽기 전용</strong>
                <p>뉴스 근거는 주문 결론이 아니다. 실거래 제출은 계속 차단된다.</p>
              </article>
              <article className="brief-signal-card">
                <span>다음 경로</span>
                <strong>추천·가상 매매</strong>
                <p>추천 상세와 가상 매매 상태에 실제 검증 단계가 연결됩니다.</p>
              </article>
            </div>
          </article>
        </div>

        <div className="btn-row decision-actions">
          <Link className="btn btn-primary" href={"/ai-evidence" as Route}>
            근거 후보 전체 보기
          </Link>
          <Link className="btn btn-secondary" href={"/ai-evidence/blocked" as Route}>
            차단 목록 보기
          </Link>
          <Link className="btn btn-secondary" href={"/recommendations" as Route}>
            추천 영향 보기
          </Link>
          <Link className="btn btn-secondary" href={"/paper-trading" as Route}>
            가상 매매 상태 보기
          </Link>
        </div>

        {unstructuredEvents.length > 0 ? (
          <details className="secondary-details">
            <summary>아직 투자 근거로 정리되지 않은 최근 뉴스 {unstructuredEvents.length}개 보기</summary>
            <div className="relationship-list">
              {unstructuredEvents.map((event) => (
                <div className="relationship-chip" key={event.event_id}>
                  <span>{koCode(event.event_type)}</span>
                  <NewsTitleBlock
                    compact
                    title={event.title}
                    koreanTitle={event.korean_title}
                    koreanSummary={event.korean_summary}
                    translationConfidence={event.translation_confidence}
                    symbol={event.symbol}
                    themeKey={event.theme_key}
                    impactDirection={formatImpactDirection(event.impact_direction)}
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
