import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import {
  getAiNewsClusters,
  getDashboardToday,
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
    return "원문 근거 없음";
  }
  if (cluster.embedded_chunk_count > 0) {
    return "원문 근거 검색 가능";
  }
  return "원문 근거 연결";
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
    return "규칙 기반 묶음";
  }
  if (cluster.extraction_run.provider === "codex_oauth") {
    return "AI 분석 묶음";
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
          ? `직접 언급 종목 ${symbols.length}개가 있다. 종목 상세에서 가격·추천·보유 상태를 이어 본다.`
          : "회사명이나 티커가 직접 잡힌 뉴스라 종목 상세와 추천 근거 후보에 바로 연결된다.",
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
      body: "신뢰도가 낮아 추천 점수에 강하게 반영하지 않고 원천 문서 검토가 먼저다.",
    };
  }
  if (cluster.event_count < 2) {
    return {
      label: "추천 영향",
      title: "단일 뉴스 근거",
      body: "뉴스 수가 적어 보조 근거로만 본다. 반복되는 흐름인지 추가 확인이 필요하다.",
    };
  }
  return {
    label: "추천 영향",
    title: "근거 후보",
    body: "추천·보유 검토에 연결될 수 있지만, 최종 판단은 점수·가격·투자 논리 검토가 결정한다.",
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
  if (summary.llm_candidate_invocation_count === 0) {
    return "개별 AI 후보 없음";
  }
  if (summary.latest_llm_invocation_status === "failed") {
    return "최근 AI 분석 실패";
  }
  if (summary.latest_llm_invocation_status === "succeeded") {
    return "최근 AI 분석 성공";
  }
  return koCode(summary.latest_llm_invocation_status);
}

function formatLlmCandidateDetail(summary: AiNewsClusterSummary) {
  if (summary.llm_candidate_invocation_count === 0) {
    return "뉴스 묶음은 저장된 규칙 기반 결과를 표시 중";
  }
  return `저장된 분석 ${summary.llm_candidate_artifact_count}건 · 성공 ${summary.llm_candidate_success_count}건 · 실패 ${summary.llm_candidate_failed_count}건`;
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
  const [dataHealthResponse, dashboardResponse, eventsResponse, newsClusterResponse] = await Promise.all([
    getDataHealth(),
    getDashboardToday(),
    getEvents({ limit: 40 }),
    getAiNewsClusters({ limit: 4 }),
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
    .slice(0, 6);
  const unstructuredEvents = events.events.filter((event) => !event.ai_evidence_id).slice(0, 3);
  const firstCandidate = aiCandidateEvents[0] ?? null;
  const firstCandidateEvidenceId = firstCandidate?.ai_evidence_id ?? null;
  const firstCluster = storedNewsClusters.clusters[0] ?? null;
  const clusterReviewGuide = [
    {
      title: "같은 흐름인가",
      body: "대표 뉴스 제목과 요약이 같은 정책·산업·기업 이슈를 말하는지 본다.",
    },
    {
      title: "종목 연결이 과하지 않은가",
      body: "회사명·티커가 직접 나오면 종목 뉴스, 그렇지 않으면 시장/테마 흐름으로 본다.",
    },
    {
      title: "추천 근거로 써도 되는가",
      body: "방향·신뢰도·원천 문서가 맞을 때만 추천과 보유 검토의 입력 후보로 본다.",
    },
  ];
  const reviewActions = [
    {
      index: "1",
      title: "뉴스 흐름 보기",
      target: firstCluster ? formatClusterHeadline(firstCluster) : "묶음 대기",
      body: "오늘 많이 반복된 이슈와 연결 종목을 먼저 본다.",
      cta: "흐름 열기",
      href: firstCluster ? clusterEvidenceHref(firstCluster) : ("/ai-evidence" as Route),
    },
    {
      index: "2",
      title: "AI 후보 대조",
      target: firstCandidate
        ? `${formatNewsSymbol(firstCandidate.symbol)} · ${koCode(firstCandidate.theme_key)}`
        : "후보 대기",
      body: "AI가 붙인 종목, 테마, 방향이 뉴스 원문과 맞는지 본다.",
      cta: "AI 상세 열기",
      href: firstCandidateEvidenceId ? (`/ai-evidence/${firstCandidateEvidenceId}` as Route) : ("/ai-evidence" as Route),
    },
    {
      index: "3",
      title: "상위 흐름 지도",
      target: `${events.summary.themes_represented}개 테마`,
      body: "거시 뉴스와 테마 뉴스가 어떤 종목군으로 내려가는지 먼저 본다.",
      cta: "흐름 지도",
      href: "/cycle-map" as Route,
    },
    {
      index: "4",
      title: "차단 후보 확인",
      target: `${events.summary.suppressed_low_signal_candidate_count}개 차단`,
      body: "추천 입력에서 빠진 뉴스가 왜 차단됐는지 확인한다.",
      cta: "차단 목록 보기",
      href: "/ai-evidence/blocked" as Route,
    },
  ];

  return (
    <div className="terminal-page intelligence-page">
      <section className="page-hero reveal" aria-labelledby="intelligence-title">
        <div>
          <div className="bento-badge">뉴스·AI 판단</div>
          <h1 className="page-title" id="intelligence-title">
            오늘 볼 뉴스 흐름과 추천 연결을 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면의 목적은 수집된 뉴스를 투자 판단에 쓰기 전에 “같은 흐름으로 묶어도 되는지”,
          “어떤 종목과 관계가 있는지”, “추천 근거로 연결됐는지”를 확인하는 것이다.
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
          <strong className="rail-word-value">{formatLlmCandidateStatus(clusterSummary)}</strong>
          <small>{formatLlmCandidateDetail(clusterSummary)}</small>
        </article>
        <article className="rail-cell">
          <span>뉴스 묶음 방식</span>
          <strong className="rail-word-value">{formatClusterModeStatus(clusterSummary)}</strong>
          <small>저장된 분석 결과만 표시</small>
        </article>
        <article className="rail-cell">
          <span>저장된 뉴스 묶음</span>
          <strong>{clusterSummary.cluster_count}</strong>
          <small>뉴스 {clusterSummary.clustered_event_count}개 연결</small>
        </article>
        <article className="rail-cell">
          <span>추천·보유 연결</span>
          <strong className="rail-ratio-value">{formatPercent(dashboard.latest_metrics.weight_coverage_ratio)}</strong>
          <small>추천·보유 판단 연결률</small>
        </article>
      </section>

      <section className="review-command-panel reveal delay-1" aria-labelledby="review-command-title">
        <div className="section-heading stacked-heading">
          <span>검토 시작</span>
          <h2 id="review-command-title">왼쪽부터 보면 오늘 검토가 끝난다</h2>
          <p>
            지금 가능한 작업은 읽기 전용 대조다. 완료/반려 저장 버튼은 아직 없으며,
            저장형 검토는 승인자와 감사 로그가 붙은 뒤 별도 화면으로 열어야 한다.
          </p>
        </div>
        <div className="review-command-grid">
          {reviewActions.map((step) => (
            <Link className="review-command-card" href={step.href} key={step.index}>
              <span>{step.index}</span>
              <strong>{step.title}</strong>
              <em>{step.target}</em>
              <small>{step.body}</small>
              <b>{step.cta}</b>
            </Link>
          ))}
        </div>
      </section>

      <section className="intelligence-board reveal delay-2" aria-labelledby="news-decision-board-title">
        <div className="section-heading stacked-heading">
          <span>뉴스 묶음 검토</span>
          <h2 id="news-decision-board-title">뉴스 흐름마다 세 가지만 본다</h2>
          <p>
            같은 흐름인지, 종목 연결이 타당한지, 추천 근거로 쓸 수 있는지만 확인한다.
            세부 원문과 AI 출력은 각 카드의 상세 화면에서 본다.
          </p>
        </div>

        <div className="cluster-review-guide" aria-label="뉴스 흐름 검토 기준">
          {clusterReviewGuide.map((item, index) => (
            <article key={item.title}>
              <span>{index + 1}</span>
              <strong>{item.title}</strong>
              <p>{item.body}</p>
            </article>
          ))}
        </div>

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

                  <div className="cluster-proof-grid" aria-label={`${koCode(cluster.theme_key)} 핵심 판단`}>
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
                    <span>대표 뉴스 2건</span>
                    <div className="relationship-list">
                      {cluster.events.slice(0, 2).map((event) => (
                        <div className="relationship-chip" key={`${cluster.evidence_id}-${event.event_id}`}>
                          <span>{koCode(event.impact_direction)}</span>
                          <NewsTitleBlock
                            compact
                            title={event.title}
                            koreanTitle={event.korean_title}
                            koreanSummary={event.korean_summary}
                            translationConfidence={event.translation_confidence}
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
                    AI 분석이 성공하면 묶음 기준과 원천 문서가 있는 분석 카드로 대체된다.
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
                            koreanTitle={event.korean_title}
                            koreanSummary={event.korean_summary}
                            translationConfidence={event.translation_confidence}
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
                <p className="relationship-empty">뉴스 수집과 AI 분석이 성공하면 이 영역에 대표 흐름이 표시된다.</p>
              </article>
            )}
          </div>
        )}
      </section>

      <section className="intelligence-board reveal delay-3" aria-labelledby="ai-candidate-queue-title">
        <div className="section-heading stacked-heading">
          <span>개별 뉴스 후보</span>
          <h2 id="ai-candidate-queue-title">AI가 구조화한 뉴스 한 건씩 확인한다</h2>
        </div>
        <p className="board-intro">
          이 목록은 뉴스 한 건에 붙은 종목, 테마, 방향, 신뢰도다. 이상하면 AI 상세와 뉴스 원문을 열어 대조한다.
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
                      koreanTitle={event.korean_title}
                      koreanSummary={event.korean_summary}
                      translationConfidence={event.translation_confidence}
                      symbol={event.symbol}
                      themeKey={event.theme_key}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                    <p>
                      {aiEvidenceLabel(event.ai_evidence_type)} · 대상 {formatNewsSymbol(event.symbol)} · 방향{" "}
                      {koCode(event.impact_direction)} · 신뢰도 {formatPercent(event.ai_evidence_confidence)}
                    </p>
                  </div>
                  <div className="review-queue-actions">
                    {evidenceLink ? <Link className="btn btn-primary" href={evidenceLink}>AI 상세</Link> : null}
                    {symbolLink ? <Link className="btn btn-secondary" href={symbolLink}>종목</Link> : null}
                    {documentLink ? <Link className="btn btn-secondary" href={documentLink}>뉴스 원문</Link> : null}
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
                    koreanTitle={event.korean_title}
                    koreanSummary={event.korean_summary}
                    translationConfidence={event.translation_confidence}
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
