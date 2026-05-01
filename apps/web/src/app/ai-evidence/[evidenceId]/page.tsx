import Link from "next/link";
import { getAiEvidenceDetail } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "AI Evidence" };

type AiEvidencePageProps = {
  params: Promise<{ evidenceId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatCost(value: number) {
  return `$${value.toFixed(4)}`;
}

export default async function AiEvidencePage({ params }: AiEvidencePageProps) {
  const { evidenceId } = await params;
  const response = await getAiEvidenceDetail(evidenceId);
  const data = response.data;

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          EVIDENCE • {data.instrument.symbol} • {data.classification.theme_key} • {data.extraction_run.prompt_version}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>AI Extraction Evidence</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              This page shows the stored AI interpretation as an audit object. The model output is traceable to source chunks and cannot change a thesis or recommendation by itself.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(59, 130, 246, 0.1)", 
            border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-blue)" }}>Quality Gate</span>
            <div style={{ fontSize: "2rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0", textTransform: "uppercase" }}>
              {data.extraction_run.status}
            </div>
            <div style={{ fontSize: "0.8rem", color: "var(--accent-blue)", fontWeight: 500 }}>
              {data.extraction_run.quality_gate}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2" style={{ background: "var(--bg-card-hover)", borderColor: "var(--border-focus)" }}>
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Event Evidence</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.title}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "16px" }}>
            <div>
              <span className="metric-sub">Evidence ID</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)" }}>{data.evidence_id}</div>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              <div>
                <span className="metric-sub">Impact Direction</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{data.classification.impact_direction}</div>
              </div>
              <div>
                <span className="metric-sub">Impact Score</span>
                <div style={{ fontSize: "1.1rem", fontWeight: 600 }}>{formatPercent(data.classification.impact_score)}</div>
              </div>
            </div>
            <div>
              <span className="metric-sub">Event Time</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{data.event_at}</div>
            </div>
            <div>
              <span className="metric-sub">Source Document</span>
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
            <span className="metric-sub">Model Provenance</span>
            <h2 style={{ fontSize: "1.5rem" }}>{data.extraction_run.provider}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">Model</span>
              <div style={{ fontSize: "1rem", fontWeight: 600, fontFamily: "monospace" }}>{data.extraction_run.model_id}</div>
            </div>
            <div style={{ gridColumn: "span 2" }}>
              <span className="metric-sub">Run ID</span>
              <div style={{ fontSize: "0.85rem", fontWeight: 500, fontFamily: "monospace", color: "var(--text-secondary)" }}>{data.extraction_run.run_id}</div>
            </div>
            <div>
              <span className="metric-sub">Tokens</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>
                <span style={{ color: "var(--accent-amber)" }}>{data.extraction_run.input_tokens} In</span>
                <span style={{ color: "var(--text-tertiary)", margin: "0 4px" }}>/</span>
                <span style={{ color: "var(--accent-green)" }}>{data.extraction_run.output_tokens} Out</span>
              </div>
            </div>
            <div>
              <span className="metric-sub">Estimated Cost</span>
              <div style={{ fontSize: "0.95rem", fontWeight: 500 }}>{formatCost(data.extraction_run.estimated_cost_usd)}</div>
            </div>
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Structured Extraction</span>
            <h2 style={{ fontSize: "1.5rem" }}>Fields with Cited Chunks</h2>
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
                <span className="metric-sub" style={{ color: "var(--accent-amber)" }}>{field.field}</span>
                <strong style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>{field.value}</strong>
                <div style={{ marginTop: "8px", fontSize: "0.75rem", color: "var(--text-tertiary)", display: "flex", justifyContent: "space-between", borderTop: "1px solid rgba(255,255,255,0.05)", paddingTop: "8px" }}>
                  <span>Conf: {formatPercent(field.confidence)}</span>
                  <span style={{ fontFamily: "monospace" }}>{field.source_chunk_id}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2 row-span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Source Chunks</span>
            <h2 style={{ fontSize: "1.5rem" }}>What the Model Saw</h2>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {data.source_chunks.map((chunk) => (
              <div key={chunk.chunk_id} style={{
                padding: "16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid var(--border-light)",
                borderRadius: "var(--radius-sm)"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong style={{ fontSize: "1rem", color: "var(--text-primary)" }}>{chunk.section}</strong>
                  <span className="bento-badge" style={{ margin: 0, padding: "2px 8px", fontSize: "0.65rem" }}>{chunk.locator}</span>
                </div>
                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 12px 0" }}>{chunk.summary}</p>
                <span style={{ fontSize: "0.7rem", color: "var(--accent-blue)", fontWeight: 600, textTransform: "uppercase" }}>Relevance: {chunk.relevance}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">Guardrails</span>
            <h2 style={{ fontSize: "1.5rem" }}>Audit Notes</h2>
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
              <li key={note} style={{ color: "var(--text-primary)" }}>{note}</li>
            ))}
          </ul>
          <div className="btn-row" style={{ marginTop: "auto" }}>
            <Link className="btn btn-secondary" href="/theses/AAPL-bootstrap-v1">
              Open Thesis
            </Link>
            <Link className="btn btn-secondary" href="/recommendations/AAPL-2024-11-01">
              Open Recommendation
            </Link>
          </div>
        </article>
      </section>
    </div>
  );
}
