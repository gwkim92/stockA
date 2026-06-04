import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { getAiEvidenceDetail, getAiEvidenceNeighborhood } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiEvidenceDetailData, AiEvidenceNeighborhoodData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "AI 근거 상세" };

type AiEvidencePageProps = {
  params: Promise<{ evidenceId: string }>;
};

type NewsCandidate = NonNullable<AiEvidenceDetailData["news_candidate"]>;
type ClusterSummary = NonNullable<AiEvidenceDetailData["cluster_summary"]>;
type EvidenceNeighborhood = AiEvidenceNeighborhoodData | null;
type ExtractedField = AiEvidenceDetailData["extracted_fields"][number];
type EvidenceTraceStep = {
  index: string;
  label: string;
  title: string;
  body: string;
  status: string;
  href?: Route | null;
  cta?: string;
  tone?: "risk-low" | "risk-medium" | "risk-high";
};

function formatPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return "미제공";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function isPlaceholderModel(value: string | null | undefined) {
  return !value || /placeholder|fixture|unknown/i.test(value);
}

function extractionRunLabel(data: AiEvidenceDetailData) {
  const provider = koCode(data.extraction_run.provider);
  if (isPlaceholderModel(data.extraction_run.model_id)) {
    return provider.includes("분석") ? provider : `${provider} 배치 분석`;
  }
  return `${provider} · ${koCode(data.extraction_run.model_id)}`;
}

function normalizeEvidenceSystemCopy(value: string | null | undefined) {
  const oldNewsAiCandidate = ["뉴스 AI", "후보"].join(" ");
  const oldAiCandidate = ["AI", "후보"].join(" ");
  const oldHoldingReview = ["보유", "검토"].join("");
  return koLabel(value)
    .replaceAll("fixture에는 AI 근거 가시성 trace가 없어 기본 경로만 표시한다.", "저장된 상세 추적 정보가 부족해 확인 가능한 경로만 표시한다.")
    .replaceAll("fixture에는 validator 상세 이유가 없다.", "자동 검증의 상세 사유가 아직 저장되지 않았다.")
    .replaceAll("fixture 기준 번역 trace가 없다.", "번역 추적 정보가 아직 저장되지 않았다.")
    .replaceAll("추천 연결 trace는 live DB에서 확인한다.", "추천 연결 정보는 최신 운영 데이터에서 확인한다.")
    .replaceAll("live DB", "최신 운영 데이터")
    .replaceAll("validator", "자동 검증")
    .replaceAll("trace", "추적 정보")
    .replaceAll("fixture", "현재 데이터")
    .replaceAll("write", "쓰기 작업")
    .replaceAll(oldNewsAiCandidate, "뉴스 AI 구조화 항목")
    .replaceAll(oldAiCandidate, "AI 구조화 항목")
    .replaceAll(oldHoldingReview, "보유 상태 판단")
    .replaceAll("입력 후보", "입력 항목")
    .replaceAll("통과 후보", "통과 항목")
    .replaceAll("검토 후보", "판단 항목")
    .replaceAll("후보 상태", "항목 상태");
}

function isKnownCode(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function primarySymbol(data: AiEvidenceDetailData) {
  const candidateSymbol = data.news_candidate?.instrument_impacts.find((impact) => isKnownCode(impact.target))?.target;
  const clusterSymbol = data.cluster_summary?.symbols.find(isKnownCode);
  const instrumentSymbol = isKnownCode(data.instrument.symbol) ? data.instrument.symbol : null;
  return candidateSymbol ?? clusterSymbol ?? instrumentSymbol ?? null;
}

function uniqueSourceDocumentCount(data: AiEvidenceDetailData) {
  return new Set(data.cluster_events.map((event) => event.source_document_id).filter(Boolean)).size;
}

function firstSourceDocumentId(data: AiEvidenceDetailData) {
  return data.source_document_id || data.cluster_events.find((event) => event.source_document_id)?.source_document_id || null;
}

function formatSymbols(symbols: string[] | null | undefined) {
  const knownSymbols = (symbols ?? []).filter(isKnownCode);
  if (knownSymbols.length === 0) {
    return "연결 종목 없음";
  }
  return knownSymbols.map(koCode).join(", ");
}

function formatDirectionCounts(directionCounts: Record<string, number> | null | undefined) {
  if (!directionCounts || Object.keys(directionCounts).length === 0) {
    return "영향 방향 미분류";
  }
  return Object.entries(directionCounts)
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([direction, count]) => `${koCode(direction)} ${count}`)
    .join(" · ");
}

function formatClusterStory(cluster: ClusterSummary) {
  const label = cluster.story_label?.trim();
  if (!label || label === cluster.theme_key || label === cluster.theme_name) {
    return koCode(cluster.theme_key);
  }
  return koLabel(label);
}

function clusterRelationReasons(data: AiEvidenceDetailData, cluster: ClusterSummary) {
  const sourceDocumentCount = new Set(
    data.cluster_events.map((event) => event.source_document_id).filter(Boolean),
  ).size;
  const symbols = cluster.symbols.filter(isKnownCode);
  const reasons = [`같은 상위 테마로 묶임: ${koCode(cluster.theme_key)}`];
  if (cluster.story_key && cluster.story_key !== "theme") {
    reasons.push(`같은 하위 이슈로 묶임: ${formatClusterStory(cluster)}`);
  }
  reasons.push(
    symbols.length > 0
      ? `직접 연결 종목: ${symbols.map(koCode).join(", ")}`
      : "직접 종목 없음: 시장/테마 흐름으로 저장하고 노출도 전파에서 종목 영향을 계산한다.",
  );
  if (cluster.event_count > 0) {
    reasons.push(`뉴스 이벤트 ${cluster.event_count}개가 같은 묶음에 연결됨`);
  }
  if (sourceDocumentCount > 0) {
    reasons.push(`원천 문서 ${sourceDocumentCount}개로 확인 가능`);
  }
  if (data.source_chunks.length > 0) {
    reasons.push(`원문 근거 ${data.source_chunks.length}개 연결`);
  }
  return reasons;
}

function formatContextCount(value: Array<Record<string, unknown>> | undefined) {
  return (value?.length ?? 0).toLocaleString("ko-KR");
}

function formatSourceSection(section: string) {
  if (section === "source") {
    return "원천 뉴스";
  }
  return koLabel(section);
}

function formatSourceLocator(locator: string) {
  if (/document chunk/i.test(locator)) {
    return "모델 입력 문서";
  }
  return koLabel(locator);
}

function inferKoreanSourceTopic(value: string) {
  const text = value.toLowerCase();
  if (/(quantum|qubit|rigetti|d-wave|ionq|qbts|qubt|ibm)/.test(text)) {
    return "양자컴퓨팅·정책 수혜";
  }
  if (/(fed|warsh|rate|rates|treasury|bond|yield|inflation|annuity)/.test(text)) {
    return "금리·연준";
  }
  if (/(oil|iran|hormuz|crude|energy|gas|xom|drilling)/.test(text)) {
    return "에너지·지정학";
  }
  if (/(nvidia|semiconductor|chip|qualcomm|skyworks|qorvo|tower semiconductor|tsem)/.test(text)) {
    return "AI 반도체 사이클";
  }
  if (/(s&p|nasdaq|dow|stock market|stocks|buffett indicator)/.test(text)) {
    return "미국 시장 참여도";
  }
  return "시장 뉴스 흐름";
}

function formatSourceSummary(summary: string) {
  const title = summary.match(/Title:\s*(.*?)(?:\s+Summary:|$)/)?.[1]?.trim();
  const body = summary.match(/Summary:\s*(.*?)(?:\s+Published\/Event At:|$)/)?.[1]?.trim();
  const eventAt = summary.match(/Published\/Event At:\s*(.*?)(?:\s+Source:|$)/)?.[1]?.trim();
  const source = summary.match(/Source:\s*(.*?)(?:\s+URL:|$)/)?.[1]?.trim();
  const topic = inferKoreanSourceTopic(`${title ?? ""} ${body ?? ""}`);
  const parts = [
    title || body ? `한국어 요약: ${topic} 관련 원천 근거` : null,
    eventAt ? `발행 시각: ${eventAt}` : null,
    source ? `출처: ${koCode(source)}` : null,
  ].filter(Boolean);
  if (parts.length > 0) {
    return parts.join(" · ");
  }
  return koLabel(summary.split(" Retrieval context:")[0] ?? summary);
}

function formatSourceRelevance(relevance: string) {
  if (relevance.toLowerCase().includes("supporting")) {
    return "근거 문맥";
  }
  return koCode(relevance);
}

function formatExtractedFieldValue(field: ExtractedField) {
  const rawValue = field.value.trim();
  const slashParts = rawValue.split(" / ").map((part) => part.trim()).filter(Boolean);
  if (slashParts.length >= 3) {
    const [target, direction, ...rest] = slashParts;
    return `${koCode(target)} · ${koCode(direction)}. ${koLabel(rest.join(" / "))}`;
  }
  return koLabel(rawValue);
}

function formatExtractedFieldLabel(fieldName: string) {
  const normalized = fieldName.trim().toLowerCase().replaceAll(" ", "_");
  if (normalized === "impact_direction") {
    return "영향 방향";
  }
  if (normalized === "event_title") {
    return "이벤트 제목";
  }
  if (normalized === "theme_mapping") {
    return "테마 매핑";
  }
  return koCode(normalized);
}

function formatExtractedFieldSource(sourceChunkId: string) {
  if (sourceChunkId === "chunk-news-ai-candidate") {
    return "뉴스 구조화 근거";
  }
  if (sourceChunkId === "chunk-news-ai-theme-impact") {
    return "테마 영향 근거";
  }
  if (sourceChunkId === "chunk-news-ai-instrument-impact") {
    return "종목 영향 근거";
  }
  if (sourceChunkId.startsWith("chunk-news-ai-")) {
    return "AI 추출 근거";
  }
  if (sourceChunkId === "chunk-mdna-services") {
    return "경영진 논의 근거";
  }
  if (sourceChunkId === "chunk-business-overview") {
    return "사업 개요 근거";
  }
  return koLabel(sourceChunkId);
}

function stockHref(symbol: string | null | undefined) {
  return isKnownCode(symbol) ? (`/stocks/${encodeURIComponent(symbol as string)}` as Route) : null;
}

function sourceHref(documentId: string | null | undefined) {
  return documentId ? (`/source-documents/${encodeURIComponent(documentId)}` as Route) : null;
}

function recommendationHref(recommendationId: string | null | undefined) {
  return recommendationId ? (`/recommendations/${encodeURIComponent(recommendationId)}` as Route) : null;
}

function thesisHref(thesisId: string | null | undefined) {
  return thesisId ? (`/theses/${encodeURIComponent(thesisId)}` as Route) : null;
}

async function loadNeighborhood(symbol: string | null): Promise<EvidenceNeighborhood> {
  if (!symbol) {
    return null;
  }
  try {
    const response = await getAiEvidenceNeighborhood(symbol);
    return response.data;
  } catch {
    return null;
  }
}

function pageCopy(data: AiEvidenceDetailData, candidate: NewsCandidate | null, cluster: ClusterSummary | null) {
  if (candidate && data.evidence_type === "news_event_candidate_rejected") {
    return {
      badge: `차단된 AI 구조화 항목 · ${koCode(data.extraction_run.provider)}`,
      title: "이 AI 구조화 항목이 왜 추천 근거로 통과하지 못했는지 확인한다.",
      lede:
        "자동 검증 단계에서 통과 가능한 종목·테마 영향으로 인정하지 않은 항목을 보는 화면이다. 원천과 AI 출력은 보존하지만 추천·보유 상태 판단 입력으로 쓰지 않는다.",
    };
  }
  if (candidate) {
    return {
      badge: `개별 뉴스 AI 구조화 항목 · ${koCode(data.extraction_run.provider)}`,
      title: "이 뉴스가 어떤 종목과 테마에 영향을 주는지 확인한다.",
      lede:
        "AI는 뉴스 한 건을 투자 행동으로 바꾸지 않는다. 여기서는 원천 뉴스, 추출된 테마·종목 영향, 신뢰도, 불확실성, 추천·보유 연결 여부만 확인한다.",
    };
  }
  if (cluster) {
    return {
      badge: `뉴스 묶음 근거 · ${koCode(data.extraction_run.provider)}`,
      title: "이 뉴스 묶음이 어떤 시장 흐름과 종목 연결로 이어졌는지 확인한다.",
      lede:
        "이 화면은 매수 판단 화면이 아니다. 같은 흐름으로 묶인 이유, 연결된 상위 테마, 종목 연결, 추천 근거 연결 여부를 원천 뉴스와 함께 대조한다.",
    };
  }
  return {
    badge: `AI 추출 근거 · ${koCode(data.extraction_run.provider)}`,
    title: "저장된 AI 근거의 원천과 품질을 확인한다.",
    lede: "이 근거 하나만으로 투자 논리나 추천을 바꾸지 않는다. 반드시 원천과 품질 조건을 함께 확인한다.",
  };
}

function providerReviewNote(data: AiEvidenceDetailData) {
  if (["local_rules", "local_deterministic"].includes(data.extraction_run.provider)) {
    return "최종 투자 판단이 아니라 무료 로컬 규칙으로 만든 묶음이다. 다음 AI 배치와 자동 검증이 원문 제목과 테마 일치 여부를 다시 점검해야 한다.";
  }
  if (data.extraction_run.provider === "codex_oauth") {
    return "AI 배치가 구조화한 결과다. 그래도 원문과 종목 연결을 대조해야 한다.";
  }
  return `${koCode(data.extraction_run.provider)} 결과다. 원천과 연결 대상을 대조해야 한다.`;
}

function evidenceDecision(data: AiEvidenceDetailData) {
  if (data.evidence_type === "news_event_candidate_rejected") {
    return {
      label: "자동 검증 차단",
      tone: "risk-high",
      body: "이 항목은 canonical 영향 테이블과 추천 입력으로 넘기지 않는다. 원천 확인과 분류 보강 대상으로만 남긴다.",
    };
  }
  if (["local_rules", "local_deterministic"].includes(data.extraction_run.provider)) {
    return {
      label: "규칙 기반 항목",
      tone: "risk-medium",
      body: "무료 로컬 규칙이 만든 근거다. AI 최종 구조화가 아니라서 같은 테마·종목 연결이 맞는지 별도 자동 검증이 확인해야 한다.",
    };
  }
  if (data.extraction_run.quality_gate === "ai_review_passed") {
    return {
      label: "AI 검증 통과 항목",
      tone: "risk-low",
      body: "구조화 결과가 저장됐고 추천·보유 상태 판단의 입력으로 사용할 수 있다. 그래도 주문 결론은 만들지 않는다.",
    };
  }
  return {
    label: koCode(data.extraction_run.quality_gate || data.extraction_run.status),
    tone: "risk-medium",
    body: "AI 구조화 결과는 저장됐지만, 추천 입력으로 쓰기 전에 원천과 연결 대상 점검이 필요하다.",
  };
}

function preferredClusterPreviewEvent(data: AiEvidenceDetailData) {
  return (
    data.cluster_events.find((event) => Boolean(event.korean_title || event.korean_summary))
    ?? data.cluster_events[0]
    ?? null
  );
}

function primarySourcePreview(data: AiEvidenceDetailData) {
  const event = preferredClusterPreviewEvent(data);
  if (event?.korean_title || event?.korean_summary) {
    return {
      title: event.title,
      koreanTitle: event.korean_title,
      koreanSummary: event.korean_summary,
      translationConfidence: event.translation_confidence,
      symbol: event.symbol,
      themeKey: data.cluster_summary?.theme_key ?? data.classification.theme_key,
      impactDirection: event.impact_direction,
      impactScore: event.impact_score,
    };
  }
  if (data.korean_title || data.korean_summary || !event) {
    return {
      title: data.title,
      koreanTitle: data.korean_title,
      koreanSummary: data.korean_summary,
      translationConfidence: data.translation_confidence,
      symbol: primarySymbol(data),
      themeKey: data.classification.theme_key,
      impactDirection: data.classification.impact_direction,
      impactScore: data.classification.impact_score,
    };
  }
  return {
    title: event.title,
    koreanTitle: event.korean_title,
    koreanSummary: event.korean_summary,
    translationConfidence: event.translation_confidence,
    symbol: event.symbol,
    themeKey: data.cluster_summary?.theme_key ?? data.classification.theme_key,
    impactDirection: event.impact_direction,
    impactScore: event.impact_score,
  };
}

function translationTraceStatus(preview: ReturnType<typeof primarySourcePreview>) {
  if (preview.koreanTitle || preview.koreanSummary) {
    return {
      title: "한국어 번역 확인",
      status: preview.translationConfidence != null ? `신뢰도 ${formatPercent(preview.translationConfidence)}` : "번역 있음",
      body: "원문을 먼저 영어로 읽지 않아도 핵심 제목과 요약을 한국어로 대조할 수 있다.",
      tone: "risk-low" as const,
    };
  }
  return {
    title: "한국어 번역 없음",
    status: "원문 확인 필요",
    body: "아직 저장된 한국어 제목/요약이 없어 원문 제목과 AI 해석을 직접 대조해야 한다.",
    tone: "risk-medium" as const,
  };
}

function aiStructureTraceStatus({
  candidate,
  cluster,
  isNewsCandidate,
  isNewsCluster,
}: {
  candidate: NewsCandidate | null;
  cluster: ClusterSummary | null;
  isNewsCandidate: boolean;
  isNewsCluster: boolean;
}) {
  if (isNewsCandidate && candidate) {
    const themeCount = candidate.theme_impacts.length;
    const instrumentCount = candidate.instrument_impacts.length;
    return {
      title: "개별 뉴스 구조화",
      status: `테마 ${themeCount} · 종목 ${instrumentCount}`,
      body: "AI가 이 뉴스 한 건에서 테마 영향과 직접 종목 영향을 분리했다.",
    };
  }
  if (isNewsCluster && cluster) {
    return {
      title: "뉴스 묶음 구조화",
      status: `뉴스 ${cluster.event_count}개`,
      body: "여러 뉴스가 같은 상위 테마나 하위 이슈인지 묶어 시장 흐름 항목으로 만들었다.",
    };
  }
  return {
    title: "구조화 결과 제한",
    status: "세부 필드 확인",
    body: "저장된 추출 필드와 모델 입력 근거를 아래 상세에서 확인해야 한다.",
  };
}

function aiEvidenceUsageVerdict({
  data,
  linkedSymbol,
  recommendationCount,
  thesisCount,
}: {
  data: AiEvidenceDetailData;
  linkedSymbol: string | null;
  recommendationCount: number;
  thesisCount: number;
}) {
  if (data.visibility_trace.validator.blocked || data.evidence_type === "news_event_candidate_rejected") {
    return {
      title: "추천 입력에서 제외한다",
      metric: "차단",
      body:
        "자동 검증이 차단한 근거다. 원천과 AI 출력은 보존하지만 추천 점수, 보유 상태 판단, 가상 매매 입력으로 넘기지 않는다.",
      next: "차단 이유와 원천을 확인하고, 좋은 뉴스가 잘못 막혔을 때만 분류 체계나 종목 별칭을 보강한다.",
      tone: "risk-high" as const,
    };
  }
  if (recommendationCount > 0) {
    return {
      title: "추천 근거로 연결됐다",
      metric: `추천 ${recommendationCount}개`,
      body:
        "자동 검증을 통과했고 추천 상세에 연결된 근거다. 그래도 추천 상세에서 가격, 사이클, 재무, thesis, 가상 매매 상태를 다시 합쳐 판단한다.",
      next: `투자 논리 ${thesisCount}개와 추천 상세를 이어서 확인한다. 이 화면은 주문을 만들지 않는다.`,
      tone: "risk-low" as const,
    };
  }
  if (linkedSymbol) {
    return {
      title: "종목 맥락까지 연결됐다",
      metric: koCode(linkedSymbol),
      body:
        "명확한 종목 맥락은 있지만 아직 추천 상세 연결은 약하다. 종목 상세에서 직접 뉴스, 상위 흐름, 투자 논리 연결을 먼저 확인한다.",
      next: "추천 점수에 반영됐다고 단정하지 말고 종목 상세에서 근거 경로를 이어서 본다.",
      tone: "risk-medium" as const,
    };
  }
  return {
    title: "시장·테마 흐름으로 보관한다",
    metric: "상위 흐름",
    body:
      "명확한 직접 종목이 없으므로 억지로 티커를 붙이지 않는다. 거시·테마 흐름으로 저장한 뒤 노출도 전파가 관련 종목 영향을 계산한다.",
    next: "흐름 보드와 사이클맵에서 상위 테마가 어떤 종목군에 전파되는지 확인한다.",
    tone: "risk-medium" as const,
  };
}

function CandidateImpactList({ candidate }: { candidate: NewsCandidate }) {
  const impacts = [
    ...candidate.theme_impacts.map((impact) => ({ ...impact, kind: "테마" })),
    ...candidate.instrument_impacts.map((impact) => ({ ...impact, kind: "종목" })),
  ];

  if (impacts.length === 0) {
    return <div className="empty-state">AI가 구조화한 테마·종목 영향 항목이 없다. 이 근거는 추천 입력으로 쓰면 안 된다.</div>;
  }

  return (
    <div className="impact-decision-list">
      {impacts.map((impact) => (
        <article className="impact-decision-card" key={`${impact.kind}-${impact.target}-${impact.impact_direction}`}>
          <span>{impact.kind}</span>
          <strong>{koCode(impact.target)}</strong>
          <p>{koLabel(impact.evidence_summary || impact.rationale)}</p>
          <small>
            {koCode(impact.impact_direction)} · 강도 {formatPercent(impact.impact_strength)} · 신뢰도{" "}
            {formatPercent(impact.confidence)}
          </small>
        </article>
      ))}
    </div>
  );
}

function NeighborhoodPanel({ neighborhood }: { neighborhood: EvidenceNeighborhood }) {
  if (!neighborhood) {
    return (
      <article className="evidence-decision-card">
        <div className="section-heading stacked-heading">
          <span>종목 연결</span>
          <h2>연결할 종목 맥락이 없다</h2>
        </div>
        <p className="board-intro">이 근거는 아직 특정 종목의 추천, 투자 논리, 보유 포지션과 연결되지 않았다.</p>
      </article>
    );
  }

  return (
    <article className="evidence-decision-card" aria-labelledby="neighborhood-title">
      <div className="section-heading stacked-heading">
        <span>종목 연결</span>
        <h2 id="neighborhood-title">{koCode(neighborhood.symbol)}에 이미 붙어 있는 투자 맥락</h2>
      </div>

      <section className="status-rail compact-rail" aria-label={`${koCode(neighborhood.symbol)} 연결 요약`}>
        <article className="rail-cell">
          <span>테마</span>
          <strong>{neighborhood.summary.theme_count}</strong>
          <small>테마 관계 연결</small>
        </article>
        <article className="rail-cell">
          <span>이벤트</span>
          <strong>{neighborhood.summary.event_count}</strong>
          <small>관련 뉴스·공시</small>
        </article>
        <article className="rail-cell">
          <span>추천</span>
          <strong>{neighborhood.summary.recommendation_count}</strong>
          <small>추천 상세 연결</small>
        </article>
        <article className="rail-cell">
          <span>보유</span>
          <strong>{neighborhood.summary.position_count}</strong>
          <small>포트폴리오 연결</small>
        </article>
      </section>

      <div className="relationship-panel">
        <span>추천·투자 논리 연결</span>
        <div className="relationship-list">
          {neighborhood.recommendations.slice(0, 3).map((recommendation) => {
            const href = recommendationHref(recommendation.recommendation_id);
            return (
              <div className="relationship-chip" key={recommendation.recommendation_id}>
                <span>{koCode(recommendation.action)}</span>
                <strong>{koCode(recommendation.bucket)} · 점수 {formatPercent(recommendation.total_score)}</strong>
                <small>{recommendation.as_of_date} · 권장 비중 {formatPercent(recommendation.recommended_weight)}</small>
                {href ? <Link href={href}>추천 상세 열기</Link> : null}
              </div>
            );
          })}
          {neighborhood.theses.slice(0, 3).map((thesis) => {
            const href = thesisHref(thesis.thesis_id);
            return (
              <div className="relationship-chip" key={thesis.thesis_id}>
                <span>투자 논리</span>
                <strong>{koLabel(thesis.title)}</strong>
                <small>
                  {koCode(thesis.status)} · 확신 {formatPercent(thesis.conviction_score)}
                </small>
                {href ? <Link href={href}>투자 논리 열기</Link> : null}
              </div>
            );
          })}
          {neighborhood.recommendations.length === 0 && neighborhood.theses.length === 0 ? (
            <p className="relationship-empty">아직 추천 상세나 투자 논리가 연결되지 않았다.</p>
          ) : null}
        </div>
      </div>

      <div className="relationship-panel">
        <span>최근 관련 이벤트</span>
        <div className="relationship-list">
          {neighborhood.events.slice(0, 4).map((event) => (
            <div className="relationship-chip" key={event.event_id}>
              <span>{koCode(event.impact_direction)}</span>
              <NewsTitleBlock
                compact
                title={event.title}
                koreanTitle={event.korean_title}
                koreanSummary={event.korean_summary}
                translationConfidence={event.translation_confidence}
                themeKey={event.theme_key}
                impactDirection={event.impact_direction}
                impactScore={event.impact_score}
              />
              <small>
                {koCode(event.theme_key)} · {event.event_at} · 영향도 {formatPercent(event.impact_score)}
              </small>
            </div>
          ))}
          {neighborhood.events.length === 0 ? <p className="relationship-empty">종목에 연결된 최근 이벤트가 없다.</p> : null}
        </div>
      </div>
    </article>
  );
}

function EvidenceTracePath({ steps }: { steps: EvidenceTraceStep[] }) {
  return (
    <section className="evidence-trace-panel reveal delay-1" aria-labelledby="evidence-trace-title">
      <div className="section-heading stacked-heading">
        <span>근거 추적 경로</span>
        <h2 id="evidence-trace-title">원천 뉴스에서 추천 연결까지 한 줄로 확인한다</h2>
        <p>아래 5단계 중 앞 단계가 흔들리면 뒤 단계는 투자 판단 입력으로 쓰지 않는다.</p>
      </div>
      <div className="evidence-trace-grid">
        {steps.map((step) => (
          <article className={`evidence-trace-card ${step.tone ?? "risk-low"}`} key={`${step.index}-${step.label}`}>
            <span>{step.index}</span>
            <strong>{step.label}</strong>
            <em>{step.title}</em>
            <b>{step.status}</b>
            <p>{step.body}</p>
            {step.href && step.cta ? <Link href={step.href}>{step.cta}</Link> : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function AiEvidenceReviewBrief({
  data,
  sourcePreview,
  sourceLink,
  targetStockLink,
  firstRecommendationLink,
  linkedSymbol,
  neighborhood,
  decision,
  candidate,
  cluster,
  isNewsCandidate,
  isNewsCluster,
}: {
  data: AiEvidenceDetailData;
  sourcePreview: ReturnType<typeof primarySourcePreview>;
  sourceLink: Route | null;
  targetStockLink: Route | null;
  firstRecommendationLink: Route | null;
  linkedSymbol: string | null;
  neighborhood: EvidenceNeighborhood;
  decision: ReturnType<typeof evidenceDecision>;
  candidate: NewsCandidate | null;
  cluster: ClusterSummary | null;
  isNewsCandidate: boolean;
  isNewsCluster: boolean;
}) {
  const translation = translationTraceStatus(sourcePreview);
  const structure = aiStructureTraceStatus({ candidate, cluster, isNewsCandidate, isNewsCluster });
  const recommendationCount = neighborhood?.summary.recommendation_count ?? 0;
  const thesisCount = neighborhood?.summary.thesis_count ?? 0;
  const usage = aiEvidenceUsageVerdict({ data, linkedSymbol, recommendationCount, thesisCount });
  const readOnlyBoundary = data.visibility_trace.read_only_boundary;
  const sourceCount = isNewsCluster ? uniqueSourceDocumentCount(data) : sourceLink ? 1 : 0;
  const cards = [
    {
      step: "01",
      label: "원천 뉴스",
      title: sourceCount > 0 ? "원천 문서 연결" : "원천 확인 필요",
      status: sourceCount > 0 ? `원천 ${sourceCount}개` : "원천 확인 필요",
      body: sourceCount > 0
        ? "AI 해석의 출발점이 되는 원천 문서가 연결되어 있다. 원천이 틀리면 뒤의 구조화와 추천 연결도 믿으면 안 된다."
        : "원천 문서가 없으면 이 근거를 추천 입력으로 쓰면 안 된다.",
      href: "#evidence-source-preview",
      cta: "원천 보기",
      tone: sourceCount > 0 ? "risk-low" as const : "risk-high" as const,
    },
    {
      step: "02",
      label: "한국어 번역",
      title: translation.title,
      status: translation.status,
      body:
        sourcePreview.koreanSummary ||
        sourcePreview.koreanTitle ||
        "저장된 한국어 제목·요약이 없으면 원문 제목과 AI 해석을 직접 대조해야 한다.",
      href: "#evidence-source-preview",
      cta: "번역 보기",
      tone: translation.tone,
    },
    {
      step: "03",
      label: "AI 구조화",
      title: structure.title,
      status: structure.status,
      body: `${structure.body} 저장된 구조화 필드 ${data.extracted_fields.length}개를 확인한다.`,
      href: "#evidence-structured-fields",
      cta: "구조화 결과 보기",
      tone: "risk-low" as const,
    },
    {
      step: "04",
      label: "자동 검증",
      title: decision.label,
      status: data.evidence_type === "news_event_candidate_rejected" ? "차단" : koCode(data.extraction_run.quality_gate || data.extraction_run.status),
      body: normalizeEvidenceSystemCopy(data.visibility_trace.validator.reasons_ko.join(" ") || decision.body),
      href: "#evidence-validation",
      cta: "검증 근거 보기",
      tone: decision.tone,
    },
    {
      step: "05",
      label: "추천·실거래 상태",
      title: usage.title,
      status: `${usage.metric} · ${koCode(readOnlyBoundary.order_boundary || "read_only_no_order")}`,
      body: `${usage.next} 증권사 주문은 ${readOnlyBoundary.broker_submit_allowed ? "허용 상태" : "차단 상태"}다.`,
      href: firstRecommendationLink ?? targetStockLink ?? "#evidence-neighborhood",
      cta: firstRecommendationLink ? "추천 보기" : targetStockLink ? "종목 보기" : "연결 상태 보기",
      tone: usage.tone,
    },
  ];

  return (
    <section className={`ai-evidence-brief-panel ${usage.tone} reveal delay-1`} aria-labelledby="ai-evidence-brief-title">
      <div className="ai-evidence-brief-lead">
        <span>이 근거의 현재 사용처</span>
        <h2 id="ai-evidence-brief-title">{usage.title}</h2>
        <p>{usage.body}</p>
        <div className="ai-evidence-brief-metrics" aria-label="AI 근거 핵심 상태">
          <div>
            <span>원천</span>
            <strong>{sourceCount > 0 ? `${sourceCount}개` : "없음"}</strong>
          </div>
          <div>
            <span>번역</span>
            <strong>{sourcePreview.koreanTitle || sourcePreview.koreanSummary ? "있음" : "없음"}</strong>
          </div>
          <div>
            <span>사용처</span>
            <strong>{usage.metric}</strong>
          </div>
          <div>
            <span>주문</span>
            <strong>{readOnlyBoundary.order_boundary ? koCode(readOnlyBoundary.order_boundary) : "차단"}</strong>
          </div>
        </div>
        <div className="ai-evidence-brief-actions">
          {sourceLink ? (
            <Link className="btn btn-primary" href={sourceLink}>
              원천 문서 열기
            </Link>
          ) : null}
          {firstRecommendationLink ? (
            <Link className="btn btn-secondary" href={firstRecommendationLink}>
              추천 상세 보기
            </Link>
          ) : null}
          {targetStockLink ? (
            <Link className="btn btn-secondary" href={targetStockLink}>
              종목 상세 보기
            </Link>
          ) : null}
        </div>
      </div>
      <div className="ai-evidence-brief-grid">
        {cards.map((card) => (
          <article className={`ai-evidence-brief-card ${card.tone}`} key={card.label}>
            <span>{card.step} · {card.label}</span>
            <strong>{card.title}</strong>
            <em>{card.status}</em>
            <p>{card.body}</p>
            {card.href.startsWith("#") ? (
              <a href={card.href}>{card.cta}</a>
            ) : (
              <Link href={card.href as Route}>{card.cta}</Link>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

function traceStatusLabel(status: string) {
  if (status === "available" || status === "passed" || status === "ready") {
    return "확인됨";
  }
  if (status === "blocked") {
    return "차단";
  }
  if (status === "needs_review" || status === "attention" || status === "limited") {
    return "추가 확인";
  }
  if (status === "missing") {
    return "부족";
  }
  if (status === "needs_neighborhood_lookup") {
    return "종목 맥락 확인";
  }
  if (status === "macro_or_theme_only") {
    return "상위 흐름";
  }
  return koCode(status);
}

function traceTone(status: string) {
  if (status === "available" || status === "passed" || status === "ready" || status === "needs_neighborhood_lookup") {
    return "risk-low";
  }
  if (status === "blocked" || status === "missing") {
    return "risk-high";
  }
  return "risk-medium";
}

function EvidenceVisibilityTraceBoard({
  data,
  neighborhood,
  sourceLink,
  targetStockLink,
  firstRecommendationLink,
}: {
  data: AiEvidenceDetailData;
  neighborhood: EvidenceNeighborhood;
  sourceLink: Route | null;
  targetStockLink: Route | null;
  firstRecommendationLink: Route | null;
}) {
  const trace = data.visibility_trace;
  const recommendationCount = neighborhood?.summary.recommendation_count ?? 0;
  const thesisCount = neighborhood?.summary.thesis_count ?? 0;
  const stepFacts: Record<string, { title: string; body: string; href?: Route | null; cta?: string }> = {
    source: {
      title: `${trace.source.source_document_count}개 원천 · ${trace.source.source_chunk_count}개 입력 근거`,
      body: normalizeEvidenceSystemCopy(trace.source.message_ko),
      href: sourceLink,
      cta: "원천 열기",
    },
    translation: {
      title: `${trace.translation.translated_event_count}개 한국어 번역`,
      body:
        trace.translation.translation_confidence != null
          ? `${normalizeEvidenceSystemCopy(trace.translation.message_ko)} 번역 신뢰도 ${formatPercent(trace.translation.translation_confidence)}.`
          : normalizeEvidenceSystemCopy(trace.translation.message_ko),
    },
    ai_structure: {
      title: `${koCode(trace.ai_structure.provider)} · ${koCode(trace.ai_structure.evidence_type)}`,
      body: `${normalizeEvidenceSystemCopy(trace.ai_structure.message_ko)} 구조화 필드 ${trace.ai_structure.extracted_field_count}개.`,
    },
    validator: {
      title: normalizeEvidenceSystemCopy(trace.validator.decision_ko),
      body: normalizeEvidenceSystemCopy(trace.validator.reasons_ko.join(" ")),
    },
    recommendation_linkage: {
      title:
        recommendationCount > 0
          ? `추천 ${recommendationCount}개 · 투자 논리 ${thesisCount}개`
          : trace.recommendation_linkage.target_symbol
            ? `${koCode(trace.recommendation_linkage.target_symbol)} 종목 맥락 확인`
            : "직접 종목 없이 상위 흐름으로 확인",
      body:
        recommendationCount > 0
          ? "연결된 추천 상세에서 가격, 사이클, 재무, 보유 논리와 함께 다시 판단한다. 이 근거는 주문 결론이 아니라 입력 근거다."
          : normalizeEvidenceSystemCopy(trace.recommendation_linkage.message_ko),
      href: firstRecommendationLink ?? targetStockLink,
      cta: firstRecommendationLink ? "추천 열기" : targetStockLink ? "종목 열기" : undefined,
    },
  };

  return (
    <section className="evidence-decision-card reveal delay-1" aria-labelledby="visibility-trace-title">
      <div className="section-heading stacked-heading">
        <span>근거 사용 경로</span>
        <h2 id="visibility-trace-title">원천 뉴스가 추천 근거로 쓰일 수 있는지 확인한다</h2>
        <p>{normalizeEvidenceSystemCopy(trace.summary_ko)}</p>
      </div>
      <div className="evidence-trace-grid">
        {trace.steps.map((step, index) => {
          const fact = stepFacts[step.step_key] ?? { title: koCode(step.step_key), body: normalizeEvidenceSystemCopy(trace.summary_ko) };
          return (
            <article className={`evidence-trace-card ${traceTone(step.status)}`} key={step.step_key}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{step.label_ko}</strong>
              <em>{fact.title}</em>
              <b>{traceStatusLabel(step.status)}</b>
              <p>{fact.body}</p>
              {fact.href && fact.cta ? <Link href={fact.href}>{fact.cta}</Link> : null}
            </article>
          );
        })}
      </div>
      <div className="relationship-panel">
        <span>검증 결과</span>
        <div className="relationship-list">
          <div className="relationship-chip">
            <span>{trace.validator.blocked ? "차단" : "통과 항목"}</span>
            <strong>{normalizeEvidenceSystemCopy(trace.validator.decision_ko)}</strong>
            <small>{normalizeEvidenceSystemCopy(trace.validator.reasons_ko.join(" "))}</small>
          </div>
          <div className="relationship-chip">
            <span>실거래 상태</span>
            <strong>읽기 전용 · 자동 주문 없음</strong>
            <small>
              화면에서는 저장된 배치 결과만 읽는다. 쓰기 기능 {trace.read_only_boundary.write_enabled ? "허용" : "차단"} ·{" "}
              {koCode(trace.read_only_boundary.order_boundary)}
            </small>
          </div>
        </div>
      </div>
    </section>
  );
}

export default async function AiEvidencePage({ params }: AiEvidencePageProps) {
  const { evidenceId } = await params;
  const response = await getAiEvidenceDetail(evidenceId);
  const data = response.data;
  const cluster = data.cluster_summary;
  const candidate = data.news_candidate;
  const isNewsCluster = data.evidence_type === "news_cluster_summary" && cluster !== null;
  const isNewsCandidate =
    ["news_event_candidate", "news_event_candidate_rejected"].includes(data.evidence_type) && candidate !== null;
  const linkedSymbol = primarySymbol(data);
  const neighborhood = await loadNeighborhood(linkedSymbol);
  const copy = pageCopy(data, isNewsCandidate ? candidate : null, isNewsCluster ? cluster : null);
  const evidenceTitle = isNewsCluster
    ? `${formatClusterStory(cluster)} 뉴스 묶음`
    : isNewsCandidate
      ? koLabel(candidate.event_summary)
      : koLabel(data.title);
  const sourceLink = sourceHref(firstSourceDocumentId(data));
  const targetStockLink = stockHref(linkedSymbol);
  const firstRecommendationLink = recommendationHref(neighborhood?.recommendations[0]?.recommendation_id);
  const decision = evidenceDecision(data);
  const sourcePreview = primarySourcePreview(data);
  const linkedSymbolLabel = linkedSymbol ? koCode(linkedSymbol) : "종목 없음";

  return (
    <div className="pageStack ai-evidence-detail-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="ai-evidence-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">{copy.badge}</span>
          <h1 className="decision-brief-title" id="ai-evidence-title">
            {copy.title}
          </h1>
          <p className="decision-brief-copy">
            {copy.lede} 근거 사용 상태는 {decision.label}이며, 원천 뉴스·한국어 번역·AI 구조화·검증·추천 연결을 아래 순서로 대조한다.
          </p>
          <div className="decision-brief-meta" aria-label="AI 근거 상세 핵심 상태">
            <span>상태 {decision.label}</span>
            <span>연결 종목 {linkedSymbolLabel}</span>
            <span>{extractionRunLabel(data)}</span>
            <span>근거 유형 {koCode(data.evidence_type)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={`decision-card ${decision.tone === "risk-low" ? "is-good" : decision.tone === "risk-medium" ? "is-watch" : "is-block"}`} href="#evidence-source-preview">
            <span>근거 사용 상태</span>
            <strong>{decision.label}</strong>
            <small>{decision.body}</small>
            <b>원천 확인</b>
          </a>
          {sourceLink ? (
            <Link className="decision-card is-good" href={sourceLink}>
              <span>원천 문서</span>
              <strong>{sourcePreview ? "문서 연결" : "문서 있음"}</strong>
              <small>원문과 한국어 요약을 대조한다.</small>
              <b>문서 열기</b>
            </Link>
          ) : (
            <a className="decision-card is-watch" href="#evidence-source-preview">
              <span>원천 문서</span>
              <strong>직접 문서 없음</strong>
              <small>화면의 원천 뉴스 요약부터 확인한다.</small>
              <b>원천 보기</b>
            </a>
          )}
          {targetStockLink ? (
            <Link className="decision-card" href={targetStockLink}>
              <span>종목 연결</span>
              <strong>{linkedSymbolLabel}</strong>
              <small>종목 상세에서 직접 뉴스와 상위 흐름을 이어서 본다.</small>
              <b>종목 보기</b>
            </Link>
          ) : (
            <a className="decision-card is-watch" href="#evidence-neighborhood">
              <span>종목 연결</span>
              <strong>종목 없음</strong>
              <small>거시·테마 뉴스는 억지로 종목에 붙이지 않는다.</small>
              <b>연결 보기</b>
            </a>
          )}
          {firstRecommendationLink ? (
            <Link className="decision-card is-good" href={firstRecommendationLink}>
              <span>추천 연결</span>
              <strong>추천 있음</strong>
              <small>추천 상세에서 이 근거가 어떻게 쓰였는지 확인한다.</small>
              <b>추천 보기</b>
            </Link>
          ) : (
            <a className="decision-card is-watch" href="#evidence-neighborhood">
              <span>추천 연결</span>
              <strong>연결 대기</strong>
              <small>검증을 통과해도 바로 주문이나 추천 채택으로 가지 않는다.</small>
              <b>연결 보기</b>
            </a>
          )}
        </div>
      </section>

      <AiEvidenceReviewBrief
        data={data}
        sourcePreview={sourcePreview}
        sourceLink={sourceLink}
        targetStockLink={targetStockLink}
        firstRecommendationLink={firstRecommendationLink}
        linkedSymbol={linkedSymbol}
        neighborhood={neighborhood}
        decision={decision}
        candidate={isNewsCandidate ? candidate : null}
        cluster={isNewsCluster ? cluster : null}
        isNewsCandidate={isNewsCandidate}
        isNewsCluster={isNewsCluster}
      />

      <EvidenceVisibilityTraceBoard
        data={data}
        neighborhood={neighborhood}
        sourceLink={sourceLink}
        targetStockLink={targetStockLink}
        firstRecommendationLink={firstRecommendationLink}
      />

      <section className="evidence-decision-card reveal delay-1" id="evidence-source-preview" aria-labelledby="source-preview-title">
        <div className="section-heading stacked-heading">
          <span>원천 뉴스</span>
          <h2 id="source-preview-title">AI가 해석한 원문을 한국어로 먼저 확인한다</h2>
        </div>
        <p className="board-intro">
          아래 제목과 요약이 AI 구조화의 출발점이다. 원천 해석이 틀리면 테마, 종목, 추천 연결도 신뢰하면 안 된다.
        </p>
        <NewsTitleBlock
          title={sourcePreview.title}
          koreanTitle={sourcePreview.koreanTitle}
          koreanSummary={sourcePreview.koreanSummary}
          translationConfidence={sourcePreview.translationConfidence}
          symbol={sourcePreview.symbol}
          themeKey={sourcePreview.themeKey}
          impactDirection={sourcePreview.impactDirection}
          impactScore={sourcePreview.impactScore}
        />
        <div className="btn-row decision-actions">
          {sourceLink ? (
            <Link className="btn btn-primary" href={sourceLink}>
              원천 문서 열기
            </Link>
          ) : null}
          {targetStockLink ? (
            <Link className="btn btn-secondary" href={targetStockLink}>
              종목 상세에서 영향 확인
            </Link>
          ) : null}
        </div>
      </section>

      <section className="evidence-decision-card reveal delay-2" aria-labelledby="evidence-main-title">
        <div className="section-heading stacked-heading">
          <span>확인 대상</span>
          <h2 id="evidence-main-title">{evidenceTitle}</h2>
        </div>

        {isNewsCandidate ? (
          <>
            <p className="board-intro">
              분석 방식: {koLabel(candidate.analysis_method)}. 추천 관련성:{" "}
              {koLabel(candidate.recommendation_relevance)}. 불확실성: {koLabel(candidate.uncertainty_notes)}
            </p>
            <CandidateImpactList candidate={candidate} />
          </>
        ) : null}

        {isNewsCluster ? (
          <>
            <p className="board-intro">
              {formatClusterStory(cluster)} 이슈의 뉴스 {cluster.event_count}개를 하나의 흐름으로 묶었다.
              상위 테마는 {koCode(cluster.theme_key)}이고, 연결 종목은 {formatSymbols(cluster.symbols)}이다.
              방향 분포는 {formatDirectionCounts(cluster.direction_counts)}이다. 아래 대표 뉴스를 보고 묶음 이유와 종목 연결이 원문과 맞는지 확인한다. {providerReviewNote(data)}
            </p>
            <div className="relationship-panel">
              <span>왜 이 뉴스들이 같이 묶였나</span>
              <div className="relationship-list">
                {clusterRelationReasons(data, cluster).map((reason) => (
                  <div className="relationship-chip" key={`${data.evidence_id}-${reason}`}>
                    <span>근거</span>
                    <strong>{reason}</strong>
                  </div>
                ))}
              </div>
            </div>
            <div className="relationship-panel">
              <span>묶음에 포함된 대표 뉴스</span>
              <div className="relationship-list">
                {data.cluster_events.map((event) => {
                  const eventSourceHref = sourceHref(event.source_document_id);
                  return (
                    <div className="relationship-chip" key={event.event_id}>
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
                        {koCode(event.symbol)} · {event.event_at} · 영향도 {formatPercent(event.impact_score)}
                      </small>
                      {eventSourceHref ? <Link href={eventSourceHref}>원천 문서 열기</Link> : null}
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        ) : null}

        {!isNewsCandidate && !isNewsCluster ? (
          <p className="board-intro">
            {koLabel(data.title)} 근거다. 원천과 품질 조건을 확인한 뒤 추천 상세 또는 보유 상태 판단과 연결해야 한다.
          </p>
        ) : null}

        <div className="btn-row decision-actions">
          {targetStockLink ? (
            <Link className="btn btn-primary" href={targetStockLink}>
              {linkedSymbolLabel} 종목 맥락 보기
            </Link>
          ) : null}
          {sourceLink ? (
            <Link className="btn btn-secondary" href={sourceLink}>
              원천 문서 열기
            </Link>
          ) : null}
          <Link className="btn btn-secondary" href="/intelligence">
            뉴스 흐름으로 돌아가기
          </Link>
        </div>
      </section>

      <section id="evidence-neighborhood">
        <NeighborhoodPanel neighborhood={neighborhood} />
      </section>

      <section className="evidence-source-grid reveal delay-3" aria-label="원천과 추출 필드">
        <article className="evidence-decision-card" id="evidence-structured-fields">
          <div className="section-heading stacked-heading">
            <span>추출 필드</span>
            <h2>AI가 남긴 구조화 필드</h2>
          </div>
          {data.extracted_fields.length > 0 ? (
            <div className="field-proof-grid">
              {data.extracted_fields.map((field) => (
                <div className="field-proof-card" key={field.field}>
                  <span>{formatExtractedFieldLabel(field.field)}</span>
                  <strong>{formatExtractedFieldValue(field)}</strong>
                  <small>
                    신뢰도 {formatPercent(field.confidence)} · {formatExtractedFieldSource(field.source_chunk_id)}
                  </small>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">저장된 구조화 필드가 없다.</div>
          )}
        </article>

        <article className="evidence-decision-card" id="evidence-model-input">
          <div className="section-heading stacked-heading">
            <span>모델 입력 근거</span>
            <h2>{isNewsCluster ? "묶음 입력" : "모델이 본 내용"}</h2>
          </div>
          {data.source_chunks.length > 0 ? (
            <div className="source-proof-list">
              {data.source_chunks.map((chunk) => (
                <div className="source-proof-card" key={chunk.chunk_id}>
                  <div>
                    <span>{formatSourceSection(chunk.section)}</span>
                    <strong>{formatSourceLocator(chunk.locator)}</strong>
                  </div>
                  <p>{formatSourceSummary(chunk.summary)}</p>
                  <small>관련성 {formatSourceRelevance(chunk.relevance)}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              {isNewsCluster
                ? "이 뉴스 묶음은 로컬 규칙과 저장 이벤트로 만든 근거라 모델 입력 조각이 없다."
                : "이 근거에 연결된 모델 입력 근거가 아직 저장되지 않았다."}
            </div>
          )}
        </article>
      </section>

      <section className="evidence-decision-card reveal delay-3" id="evidence-validation" aria-labelledby="audit-title">
        <div className="section-heading stacked-heading">
          <span>안전장치</span>
          <h2 id="audit-title">이 근거를 그대로 주문으로 쓰면 안 되는 이유</h2>
        </div>
        <ul className="audit-note-list">
          {data.audit_notes.map((note) => (
            <li key={note}>{koLabel(note)}</li>
          ))}
          <li>AI는 추천과 주문을 직접 결정하지 않는다. 추천 점수, 보유 상태 판단, 거래 안전 조건이 별도로 통과해야 한다.</li>
          <li>화면 진입 시 실시간 AI 호출은 하지 않으며, 배치가 저장한 결과만 읽는다.</li>
        </ul>
        <div className="audit-metadata">
          <details>
            <summary>모델 실행 기록 보기</summary>
            <dl>
              <div>
                <dt>실행 ID</dt>
                <dd>{data.extraction_run.run_id}</dd>
              </div>
              <div>
                <dt>프롬프트 버전</dt>
                <dd>{data.extraction_run.prompt_version}</dd>
              </div>
              <div>
                <dt>토큰</dt>
                <dd>
                  입력 {data.extraction_run.input_tokens} · 출력 {data.extraction_run.output_tokens}
                </dd>
              </div>
              <div>
                <dt>저장 문맥 조회</dt>
                <dd>
                  테마 {formatContextCount(data.retrieval_context_summary.known_themes)}개 · 관계{" "}
                  {formatContextCount(data.retrieval_context_summary.theme_edges)}개 · 유사 뉴스{" "}
                  {formatContextCount(data.retrieval_context_summary.recent_similar_events)}개
                </dd>
              </div>
            </dl>
          </details>
        </div>
      </section>
    </div>
  );
}
