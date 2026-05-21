import Link from "next/link";
import { getAiEvidenceDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "AI 근거 상세" };

type AiEvidencePageProps = {
  params: Promise<{ evidenceId: string }>;
};

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

function formatSymbols(symbols: string[] | null | undefined) {
  if (!symbols || symbols.length === 0) {
    return "연결 종목 없음";
  }
  return symbols.map(koCode).join(", ");
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

export default async function AiEvidencePage({ params }: AiEvidencePageProps) {
  const { evidenceId } = await params;
  const response = await getAiEvidenceDetail(evidenceId);
  const data = response.data;
  const cluster = data.cluster_summary;
  const candidate = data.news_candidate;
  const isNewsCluster = data.evidence_type === "news_cluster_summary" && cluster !== null;
  const isNewsCandidate = data.evidence_type === "news_event_candidate" && candidate !== null;
  const evidenceTitle = isNewsCluster
    ? `${koCode(cluster.theme_key)} 뉴스 묶음 증거`
    : isNewsCandidate
      ? candidate.event_summary
      : koLabel(data.title);
  const pageTitle = isNewsCluster ? "뉴스 묶음 증거" : isNewsCandidate ? "뉴스 AI 후보 근거" : "AI 추출 증거";
  const pageDescription = isNewsCluster
    ? "무료 RSS 뉴스를 로컬 규칙으로 묶어 저장한 감사 증거다. 유료 API나 LLM 호출 없이 어떤 뉴스들이 같은 테마로 연결됐는지 확인한다."
    : isNewsCandidate
      ? "Codex OAuth batch가 뉴스 한 건을 테마, 종목, 방향, 불확실성으로 구조화한 후보 증거다. validator를 통과한 영향만 canonical event impact로 반영된다."
      : "저장된 AI 해석을 감사 가능한 증거 객체로 보여준다. 모델 출력은 원천 청크까지 추적 가능하며, 단독으로 투자 논리나 추천을 바꿀 수 없다.";

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          {pageTitle} • {data.instrument.symbol} • {koCode(data.classification.theme_key)} • {koCode(data.extraction_run.provider)}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{pageTitle}</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              {pageDescription}
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(59, 130, 246, 0.1)", 
            border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-blue)" }}>품질 관문</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {koCode(data.extraction_run.status)}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-blue)", fontWeight: 500 }}>
              {koCode(data.extraction_run.quality_gate)}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">이벤트 증거</span>
            <h2 style={{ fontSize: "1.5rem" }}>{evidenceTitle}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">증거 식별자</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)" }}>{data.evidence_id}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <span className="metric-sub">영향 방향</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{koCode(data.classification.impact_direction)}</div>
              </div>
              <div>
                <span className="metric-sub">영향 점수</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{formatPercent(data.classification.impact_score)}</div>
              </div>
            </div>
            <div>
              <span className="metric-sub">이벤트 시각</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.event_at}</div>
            </div>
            <div>
              <span className="metric-sub">원천 문서</span>
              <Link href={`/source-documents/${data.source_document_id}`} style={{
                display: "block",
                color: "var(--accent-blue)",
                fontSize: "0.95rem",
                textDecoration: "underline",
                textUnderlineOffset: "3px",
                marginTop: "4px",
                fontFamily: "monospace"
              }}>
                {data.source_document_id}
              </Link>
            </div>
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">모델 출처</span>
            <h2 style={{ fontSize: "1.5rem" }}>{koCode(data.extraction_run.provider)}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">모델</span>
              <div style={{ fontSize: "1rem", fontWeight: 600, fontFamily: "monospace" }}>{data.extraction_run.model_id}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">실행 식별자</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)" }}>{data.extraction_run.run_id}</div>
            </div>
            <div>
              <span className="metric-sub">토큰</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>
                <span style={{ color: "var(--accent-amber)" }}>입력 {data.extraction_run.input_tokens}</span>
                <span style={{ color: "var(--text-tertiary)", margin: "0 4px" }}>/</span>
                <span style={{ color: "var(--accent-green)" }}>출력 {data.extraction_run.output_tokens}</span>
              </div>
            </div>
            <div>
              <span className="metric-sub">추정 비용</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{formatCost(data.extraction_run.estimated_cost_usd)}</div>
            </div>
          </div>
        </article>

        {isNewsCluster ? (
          <article className="bento-card span-4" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
            <div style={{ marginBottom: "24px" }}>
              <span className="metric-sub">뉴스 묶음 분석</span>
              <h2 style={{ fontSize: "1.5rem" }}>{koCode(cluster.theme_key)} 연결 지도</h2>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.6, marginTop: "8px" }}>
                같은 테마로 묶인 뉴스 {cluster.event_count}개를 저장한 증거다. 이 증거는 추천이나 주문이 아니라,
                사람이 검토할 연결 구조와 근거를 남긴다.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", marginBottom: "24px" }}>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">뉴스 수</span>
                <strong style={{ display: "block", fontSize: "1.7rem" }}>{cluster.event_count}</strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">연결 종목</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>{formatSymbols(cluster.symbols)}</strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">영향 분포</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>{formatDirectionCounts(cluster.direction_counts)}</strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">비용 경계</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>
                  토큰 {data.extraction_run.input_tokens}개 · 비용 {formatCost(data.extraction_run.estimated_cost_usd)}
                </strong>
              </div>
            </div>

            <div style={{ display: "grid", gap: "12px" }}>
              <span className="metric-sub">대표 뉴스</span>
              {data.cluster_events.map((event) => (
                <div key={event.event_id} style={{
                  padding: "16px",
                  border: "1px solid var(--border-light)",
                  borderRadius: "var(--radius-sm)",
                  background: "rgba(255, 255, 255, 0.02)",
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap", marginBottom: "8px" }}>
                    <span className="metric-sub">
                      {koCode(event.symbol)} · {event.event_at} · {koCode(event.impact_direction)}
                    </span>
                    <span className="metric-sub">영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <strong style={{ display: "block", color: "var(--text-primary)", lineHeight: 1.45 }}>{koLabel(event.title)}</strong>
                  <Link
                    href={`/source-documents/${event.source_document_id}`}
                    style={{ display: "inline-block", marginTop: "10px", color: "var(--accent-blue)", fontSize: "0.85rem", fontWeight: 700 }}
                  >
                    원천 문서 열기
                  </Link>
                </div>
              ))}
            </div>
          </article>
        ) : null}

        {isNewsCandidate ? (
          <article className="bento-card span-4" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
            <div style={{ marginBottom: "24px" }}>
              <span className="metric-sub">뉴스 AI 후보</span>
              <h2 style={{ fontSize: "1.5rem" }}>{koLabel(candidate.event_summary)}</h2>
              <p style={{ color: "var(--text-secondary)", lineHeight: 1.6, marginTop: "8px" }}>
                이 결과는 AI가 최종 추천을 만든 것이 아니라, 뉴스가 어떤 테마와 종목에 어떤 방향으로 영향을 줄 수 있는지
                후보로 구조화한 것이다. confidence, unknown theme/symbol, 영향 방향은 validator가 다시 검사한다.
              </p>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "14px", marginBottom: "24px" }}>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">분석 방식</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>{koCode(candidate.analysis_method)}</strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">추천 관련성</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>{koCode(candidate.recommendation_relevance)}</strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">조회 테마</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>
                  {formatContextCount(data.retrieval_context_summary.known_themes)}개
                </strong>
              </div>
              <div style={{ padding: "16px", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <span className="metric-sub">유사 뉴스</span>
                <strong style={{ display: "block", fontSize: "1rem", lineHeight: 1.5 }}>
                  {formatContextCount(data.retrieval_context_summary.recent_similar_events)}개
                </strong>
              </div>
            </div>

            <div className="trace-chain" aria-label="뉴스 AI 후보 검증 흐름">
              <div className="trace-node">
                <span>수집</span>
                <strong>RSS 뉴스</strong>
                <p>{koLabel(data.title)}</p>
              </div>
              <div className="trace-arrow" aria-hidden="true">→</div>
              <div className="trace-node">
                <span>RAG-lite</span>
                <strong>Postgres context</strong>
                <p>
                  테마 {formatContextCount(data.retrieval_context_summary.known_themes)}개 · 관계{" "}
                  {formatContextCount(data.retrieval_context_summary.theme_edges)}개 · 기존 영향{" "}
                  {formatContextCount(data.retrieval_context_summary.current_event_impacts)}개
                </p>
              </div>
              <div className="trace-arrow" aria-hidden="true">→</div>
              <div className="trace-node">
                <span>AI 후보</span>
                <strong>{koCode(data.extraction_run.provider)}</strong>
                <p>테마 {candidate.theme_impacts.length}개 · 종목 {candidate.instrument_impacts.length}개</p>
              </div>
              <div className="trace-arrow" aria-hidden="true">→</div>
              <div className="trace-node trace-node-final">
                <span>검증</span>
                <strong>canonical impact 반영</strong>
                <p>{koLabel(candidate.uncertainty_notes)}</p>
              </div>
            </div>

            <div className="relationship-panel" aria-label="뉴스 AI 후보 영향">
              <span>테마와 종목 영향 후보</span>
              <div className="relationship-list">
                {candidate.theme_impacts.map((impact) => (
                  <div className="relationship-chip" key={`theme-${impact.target}-${impact.impact_direction}`}>
                    <span>{koCode(impact.impact_direction)}</span>
                    <strong>{koCode(impact.target)}</strong>
                    <small>
                      강도 {formatPercent(impact.impact_strength)} · 신뢰도 {formatPercent(impact.confidence)}
                    </small>
                    <small>{koLabel(impact.evidence_summary || impact.rationale)}</small>
                  </div>
                ))}
                {candidate.instrument_impacts.map((impact) => (
                  <div className="relationship-chip" key={`instrument-${impact.target}-${impact.impact_direction}`}>
                    <span>{koCode(impact.impact_direction)}</span>
                    <strong>{koCode(impact.target)}</strong>
                    <small>
                      강도 {formatPercent(impact.impact_strength)} · 신뢰도 {formatPercent(impact.confidence)}
                    </small>
                    <small>{koLabel(impact.evidence_summary || impact.rationale)}</small>
                  </div>
                ))}
              </div>
            </div>
          </article>
        ) : null}

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">구조화 추출</span>
            <h2 style={{ fontSize: "1.5rem" }}>{isNewsCluster ? "저장된 묶음 필드" : "원천 청크로 추적되는 필드"}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
            {data.extracted_fields.map((field) => (
              <div key={field.field} style={{
                padding: "20px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)",
                display: "flex",
                flexDirection: "column",
                gap: "8px"
              }}>
                <span className="metric-sub" style={{ color: "var(--accent-amber)" }}>{koCode(field.field)}</span>
                <strong style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>{koLabel(field.value)}</strong>
                <div style={{ marginTop: "8px", fontSize: "0.75rem", color: "var(--text-tertiary)", display: "flex", justifyContent: "space-between", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "8px" }}>
                  <span>신뢰도: {formatPercent(field.confidence)}</span>
                  <span style={{ fontFamily: "monospace" }}>{field.source_chunk_id}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2 row-span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">원천 청크</span>
            <h2 style={{ fontSize: "1.5rem" }}>{isNewsCluster ? "로컬 규칙 입력" : "모델이 본 내용"}</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {data.source_chunks.length > 0 ? data.source_chunks.map((chunk) => (
              <div key={chunk.chunk_id} style={{
                padding: "16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{koLabel(chunk.section)}</strong>
                  <span className="bento-badge" style={{ margin: 0, padding: "2px 8px", fontSize: "0.65rem" }}>{chunk.locator}</span>
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 12px 0" }}>{koLabel(chunk.summary)}</p>
                <span style={{ fontSize: "0.7rem", color: "var(--accent-blue)", fontWeight: 600, textTransform: "uppercase" }}>관련성: {koCode(chunk.relevance)}</span>
              </div>
            )) : (
              <div style={{ padding: "16px", background: "rgba(255, 255, 255, 0.02)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
                <strong style={{ display: "block", marginBottom: "8px", color: "var(--text-primary)" }}>
                  {isNewsCluster ? "LLM 원천 청크 없음" : "원천 청크 없음"}
                </strong>
                <p style={{ margin: 0, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                  {isNewsCluster
                    ? "이 뉴스 묶음은 저장된 RSS 이벤트와 로컬 규칙으로 만든 증거라 모델 입력 청크가 없다."
                    : "이 증거에 연결된 원천 청크가 아직 저장되지 않았다."}
                </p>
              </div>
            )}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">안전장치</span>
            <h2 style={{ fontSize: "1.5rem" }}>감사 메모</h2>
          </div>
          <ul style={{ 
            margin: "0 0 24px 0", 
            paddingLeft: "20px", 
            color: "var(--text-secondary)", 
            display: "flex", 
            flexDirection: "column", 
            gap: "12px",
            lineHeight: 1.6
          }}>
            {data.audit_notes.map((note) => (
              <li key={note} style={{ color: "var(--text-primary)" }}>{koLabel(note)}</li>
            ))}
          </ul>
          <div className="btn-row" style={{ marginTop: "auto" }}>
            <Link className="btn btn-secondary" href={isNewsCluster || isNewsCandidate ? "/intelligence" : "/theses/AAPL-bootstrap-v1"}>
              {isNewsCluster || isNewsCandidate ? "분석 지도 열기" : "투자 논리 열기"}
            </Link>
            <Link className="btn btn-secondary" href={isNewsCluster || isNewsCandidate ? "/events" : "/recommendations/AAPL-2024-11-01"}>
              {isNewsCluster || isNewsCandidate ? "이벤트 원장 열기" : "추천 열기"}
            </Link>
          </div>
        </article>
      </section>
    </div>
  );
}
