import Link from "next/link";
import type { Route } from "next";

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

function formatPercent(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return "미제공";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function formatCost(value: number | null | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return "미제공";
  }
  return `$${value.toFixed(4)}`;
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

function formatContextCount(value: Array<Record<string, unknown>> | undefined) {
  return (value?.length ?? 0).toLocaleString("ko-KR");
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
  if (candidate) {
    return {
      badge: `개별 뉴스 AI 후보 · ${koCode(data.extraction_run.provider)}`,
      title: "이 뉴스가 어떤 종목과 테마에 영향을 주는지 검증한다.",
      lede:
        "AI는 뉴스 한 건을 투자 행동으로 바꾸지 않는다. 여기서는 원천 뉴스, 추출된 테마·종목 영향, 신뢰도, 불확실성, 추천·보유 연결 여부만 확인한다.",
    };
  }
  if (cluster) {
    return {
      badge: `뉴스 묶음 증거 · ${koCode(data.extraction_run.provider)}`,
      title: "여러 뉴스를 하나의 테마 흐름으로 묶은 근거를 검증한다.",
      lede:
        "뉴스 묶음은 시장 흐름을 빠르게 읽기 위한 보조 증거다. 추천이나 주문 결론이 아니라, 어떤 뉴스가 함께 움직였는지 확인하는 화면이다.",
    };
  }
  return {
    badge: `AI 추출 증거 · ${koCode(data.extraction_run.provider)}`,
    title: "저장된 AI 근거의 원천과 품질을 확인한다.",
    lede: "이 증거 하나만으로 투자 논리나 추천을 바꾸지 않는다. 반드시 원천과 품질 관문을 함께 확인한다.",
  };
}

function CandidateImpactList({ candidate }: { candidate: NewsCandidate }) {
  const impacts = [
    ...candidate.theme_impacts.map((impact) => ({ ...impact, kind: "테마" })),
    ...candidate.instrument_impacts.map((impact) => ({ ...impact, kind: "종목" })),
  ];

  if (impacts.length === 0) {
    return <div className="empty-state">AI가 구조화한 테마·종목 영향 후보가 없다. 이 증거는 추천 입력으로 쓰면 안 된다.</div>;
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
        <p className="board-intro">이 증거는 아직 특정 종목의 추천, 투자 논리, 보유 포지션과 연결되지 않았다.</p>
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
          <small>검토서 연결</small>
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
                {href ? <Link href={href}>추천 검토서 열기</Link> : null}
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
            <p className="relationship-empty">아직 추천 검토서나 투자 논리가 연결되지 않았다.</p>
          ) : null}
        </div>
      </div>

      <div className="relationship-panel">
        <span>최근 관련 이벤트</span>
        <div className="relationship-list">
          {neighborhood.events.slice(0, 4).map((event) => (
            <div className="relationship-chip" key={event.event_id}>
              <span>{koCode(event.impact_direction)}</span>
              <strong>{koLabel(event.title)}</strong>
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

export default async function AiEvidencePage({ params }: AiEvidencePageProps) {
  const { evidenceId } = await params;
  const response = await getAiEvidenceDetail(evidenceId);
  const data = response.data;
  const cluster = data.cluster_summary;
  const candidate = data.news_candidate;
  const isNewsCluster = data.evidence_type === "news_cluster_summary" && cluster !== null;
  const isNewsCandidate = data.evidence_type === "news_event_candidate" && candidate !== null;
  const targetSymbol = primarySymbol(data);
  const neighborhood = await loadNeighborhood(targetSymbol);
  const copy = pageCopy(data, isNewsCandidate ? candidate : null, isNewsCluster ? cluster : null);
  const evidenceTitle = isNewsCluster
    ? `${koCode(cluster.theme_key)} 뉴스 묶음`
    : isNewsCandidate
      ? koLabel(candidate.event_summary)
      : koLabel(data.title);
  const sourceLink = sourceHref(data.source_document_id);
  const targetStockLink = stockHref(targetSymbol);

  return (
    <div className="pageStack ai-evidence-detail-page">
      <section className="page-hero evidence-decision-hero reveal" aria-labelledby="ai-evidence-title">
        <div>
          <div className="bento-badge">{copy.badge}</div>
          <h1 className="page-title" id="ai-evidence-title">
            {copy.title}
          </h1>
          <p className="page-lede">{copy.lede}</p>
        </div>
        <aside className="quality-decision-card" aria-label="AI 근거 품질">
          <span>품질 관문</span>
          <strong>{koCode(data.extraction_run.quality_gate || data.extraction_run.status)}</strong>
          <p>
            {koCode(data.extraction_run.provider)} · {koCode(data.extraction_run.model_id)} · 비용{" "}
            {formatCost(data.extraction_run.estimated_cost_usd)}
          </p>
        </aside>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="AI 근거 핵심 요약">
        <article className="rail-cell">
          <span>대상</span>
          <strong>{targetSymbol ? koCode(targetSymbol) : koCode(data.classification.theme_key)}</strong>
          <small>{targetStockLink ? "종목 상세 연결됨" : "테마 중심 증거"}</small>
        </article>
        <article className="rail-cell">
          <span>영향 방향</span>
          <strong>{koCode(data.classification.impact_direction)}</strong>
          <small>영향도 {formatPercent(data.classification.impact_score)}</small>
        </article>
        <article className="rail-cell">
          <span>추천 연결</span>
          <strong>{neighborhood?.summary.recommendation_count ?? 0}</strong>
          <small>이 종목에 연결된 검토서</small>
        </article>
        <article className="rail-cell">
          <span>원천 문서</span>
          <strong>{sourceLink ? "있음" : "없음"}</strong>
          <small>{data.event_at}</small>
        </article>
      </section>

      <section className="flow-panel reveal delay-1" aria-labelledby="evidence-reading-order">
        <div className="section-heading flow-heading">
          <span>읽는 순서</span>
          <h2 id="evidence-reading-order">이 증거는 네 단계로 검증한다</h2>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>01</span>
            <strong>원천 확인</strong>
            <p>RSS 뉴스나 공시 원문이 실제로 존재하는지 먼저 본다.</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>AI 추출 확인</strong>
            <p>테마, 종목, 방향, 불확실성이 원문과 맞는지 본다.</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>종목 맥락 확인</strong>
            <p>이미 있는 추천, 투자 논리, 보유 포지션과 연결되는지 본다.</p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>투자 입력 여부 결정</strong>
            <p>품질 관문을 통과한 근거만 추천·보유 검토의 입력 후보가 된다.</p>
          </article>
        </div>
      </section>

      <section className="evidence-decision-card reveal delay-2" aria-labelledby="evidence-main-title">
        <div className="section-heading stacked-heading">
          <span>판단 대상</span>
          <h2 id="evidence-main-title">{evidenceTitle}</h2>
        </div>

        {isNewsCandidate ? (
          <>
            <p className="board-intro">
              분석 방식은 {koCode(candidate.analysis_method)}이고, 추천 관련성은{" "}
              {koCode(candidate.recommendation_relevance)}로 표시됐다. 불확실성: {koLabel(candidate.uncertainty_notes)}
            </p>
            <CandidateImpactList candidate={candidate} />
          </>
        ) : null}

        {isNewsCluster ? (
          <>
            <p className="board-intro">
              {koCode(cluster.theme_key)} 테마의 뉴스 {cluster.event_count}개를 하나의 흐름으로 묶었다.
              연결 종목은 {formatSymbols(cluster.symbols)}이고, 방향 분포는 {formatDirectionCounts(cluster.direction_counts)}이다.
            </p>
            <div className="relationship-panel">
              <span>묶음에 포함된 대표 뉴스</span>
              <div className="relationship-list">
                {data.cluster_events.map((event) => {
                  const eventSourceHref = sourceHref(event.source_document_id);
                  return (
                    <div className="relationship-chip" key={event.event_id}>
                      <span>{koCode(event.impact_direction)}</span>
                      <strong>{koLabel(event.title)}</strong>
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
            {koLabel(data.title)} 증거다. 원천과 품질 관문을 확인한 뒤 추천 또는 보유 검토와 연결해야 한다.
          </p>
        ) : null}

        <div className="btn-row decision-actions">
          {targetStockLink ? (
            <Link className="btn btn-primary" href={targetStockLink}>
              종목 상세 열기
            </Link>
          ) : null}
          {sourceLink ? (
            <Link className="btn btn-secondary" href={sourceLink}>
              원천 문서 열기
            </Link>
          ) : null}
          <Link className="btn btn-secondary" href="/intelligence">
            뉴스 AI 판단으로 돌아가기
          </Link>
        </div>
      </section>

      <NeighborhoodPanel neighborhood={neighborhood} />

      <section className="evidence-source-grid reveal delay-3" aria-label="원천과 추출 필드">
        <article className="evidence-decision-card">
          <div className="section-heading stacked-heading">
            <span>추출 필드</span>
            <h2>AI가 남긴 구조화 필드</h2>
          </div>
          {data.extracted_fields.length > 0 ? (
            <div className="field-proof-grid">
              {data.extracted_fields.map((field) => (
                <div className="field-proof-card" key={field.field}>
                  <span>{koCode(field.field)}</span>
                  <strong>{koLabel(field.value)}</strong>
                  <small>
                    신뢰도 {formatPercent(field.confidence)} · 청크 {field.source_chunk_id}
                  </small>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">저장된 구조화 필드가 없다.</div>
          )}
        </article>

        <article className="evidence-decision-card">
          <div className="section-heading stacked-heading">
            <span>원천 청크</span>
            <h2>{isNewsCluster ? "묶음 입력" : "모델이 본 내용"}</h2>
          </div>
          {data.source_chunks.length > 0 ? (
            <div className="source-proof-list">
              {data.source_chunks.map((chunk) => (
                <div className="source-proof-card" key={chunk.chunk_id}>
                  <div>
                    <span>{koLabel(chunk.section)}</span>
                    <strong>{chunk.locator}</strong>
                  </div>
                  <p>{koLabel(chunk.summary)}</p>
                  <small>관련성 {koCode(chunk.relevance)}</small>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">
              {isNewsCluster
                ? "이 뉴스 묶음은 로컬 규칙과 저장 이벤트로 만든 증거라 모델 입력 청크가 없다."
                : "이 증거에 연결된 원천 청크가 아직 저장되지 않았다."}
            </div>
          )}
        </article>
      </section>

      <section className="evidence-decision-card reveal delay-3" aria-labelledby="audit-title">
        <div className="section-heading stacked-heading">
          <span>안전장치</span>
          <h2 id="audit-title">이 근거를 그대로 주문으로 쓰면 안 되는 이유</h2>
        </div>
        <ul className="audit-note-list">
          {data.audit_notes.map((note) => (
            <li key={note}>{koLabel(note)}</li>
          ))}
          <li>AI는 추천과 주문을 직접 결정하지 않는다. 추천 점수, 보유 검토, 거래 안전 관문이 별도로 통과해야 한다.</li>
          <li>화면 진입 시 실시간 LLM 호출은 하지 않으며, 배치가 저장한 결과만 읽는다.</li>
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
